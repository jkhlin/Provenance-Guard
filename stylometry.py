"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics

TTR_WINDOW = 50

# How each measure becomes a 0-1 "more AI-like" part, and how much it counts.
#
# Only sentence-length spread counts for now. On the eight texts I measured
# (see README), spread separated AI from human and the other two did not:
# type-token ratio was HIGHEST on the clearly-AI paragraph, and punctuation
# density ran 0.04-0.09 for AI against 0.07 for human, with a plain human
# paragraph at 0.00 because it used only full stops. Counting punctuation would
# have penalised exactly the writer the service most needs to protect. Both
# stay implemented and printed; give them weight here once real data earns it.
SPREAD_HUMAN = 0.60   # coefficient of variation at or above this reads fully human
SPREAD_AI = 0.20      # at or below this reads fully AI
STYLE_WEIGHTS = {"spread": 1.0, "ttr": 0.0, "punctuation": 0.0}

# Spread from two or three sentences is mostly luck. Below this many sentences
# the spread part is pulled toward 0.5 in proportion to how few there are.
SENTENCES_FOR_FULL_TRUST = 7


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies. ← TODO

    Returns:
        A float. Decide yourself what scale it's on and which direction means
        "more human" — then write that down, because your combining rule
        depends on knowing it.

    A hint on what you're reaching for: the standard deviation of sentence
    lengths, probably divided by the mean so a long text and a short one are
    comparable. `statistics.stdev` is imported for you.

    Watch the edge case: a one-sentence submission has no spread at all, and
    `stdev` raises on fewer than two values. Decide what that should return
    before the attack set decides for you.
    """
    lengths = [len(words(sentence)) for sentence in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    # One sentence has no spread to measure. 0.0 is "none", which on its own
    # would read as machine-even, so style_signal checks the count first.
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    return statistics.stdev(lengths) / mean


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words. ← TODO

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary.

    Worth knowing before you rely on it: this measure falls as text gets
    longer, because common words repeat. Two texts of different lengths aren't
    directly comparable on it, and if your test inputs vary a lot in length,
    that alone can look like a signal.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    # Moving-average TTR: the ratio inside every 50-word window, averaged. A
    # plain ratio falls as text gets longer, so a 300-word piece would look
    # less varied than a 60-word one for no reason but length. Windowing makes
    # texts of different lengths comparable. Under 50 words it's the plain ratio.
    window = min(TTR_WINDOW, len(tokens))
    ratios = [
        len(set(tokens[i:i + window])) / window
        for i in range(len(tokens) - window + 1)
    ]
    return sum(ratios) / len(ratios)


def punctuation_density(text: str) -> float:
    """
    How much punctuation, relative to length. ← TODO

    Returns:
        A float. Whether you count all punctuation or only some kinds — commas,
        semicolons, dashes — is a real choice. Semicolons and em dashes are
        more interesting than full stops, because they vary more between
        writers.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    # Everything except the full stop: commas, semicolons, colons, dashes,
    # brackets, quotes, question and exclamation marks. A hyphen inside a word
    # (well-known) isn't punctuation here; one standing alone as a dash is.
    marks = re.findall(r"[,;:()\"?!—–]|(?<=\s)-(?=\s)", text)
    return len(marks) / len(tokens)


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    The style signal as a 0-1 score. **Higher means more likely AI**, the same
    direction as `detector.model_signal`.

    Directions: low sentence-length spread reads AI-like, so it is flipped.
    Each measure is mapped onto 0-1 before weighting (`STYLE_WEIGHTS`), so none
    wins just by having bigger raw numbers. Only spread has weight today.

    A text of two or three sentences has a spread that means very little, so
    that part is blended toward 0.5 until there are `SENTENCES_FOR_FULL_TRUST`
    sentences. The measure can't read: see the module docstring for what that
    costs.
    """
    n_sentences = len(sentences(text))

    spread = sentence_length_spread(text)
    spread_part = (SPREAD_HUMAN - spread) / (SPREAD_HUMAN - SPREAD_AI)
    spread_part = min(max(spread_part, 0.0), 1.0)
    trust = min(1.0, max(n_sentences - 1, 0) / (SENTENCES_FOR_FULL_TRUST - 1))
    spread_part = trust * spread_part + (1 - trust) * 0.5

    # Not weighted yet (see STYLE_WEIGHTS), but wired so turning one on is a
    # one-number change. Both map "less varied" to "more AI-like".
    ttr_part = min(max((0.90 - type_token_ratio(text)) / 0.30, 0.0), 1.0)
    punctuation_part = min(max(1.0 - punctuation_density(text) / 0.10, 0.0), 1.0)

    parts = {"spread": spread_part, "ttr": ttr_part, "punctuation": punctuation_part}
    total = sum(STYLE_WEIGHTS.values())
    score = sum(STYLE_WEIGHTS[k] * parts[k] for k in parts) / total
    return round(min(max(score, 0.0), 1.0), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
