"""
Turning two numbers into one, and one number into something a person can read.
← YOU BUILD THIS IN MILESTONES 4 AND 5

Two functions live here, and both are stubs.

`combine_signals` is where your false-positive decision from Milestone 1
actually gets made. Everything above it — the labels, the appeal path — is
downstream of a number this function produced.

`score_to_label` is where you stop writing for a machine and start writing for
a person. A score of 0.62 means nothing to a writer.

⚠️ Your README's **Signals and Scoring** section has to name the file and
function holding your combining rule. The grader checks your code against what
you claim, so that line should read `scoring.py::combine_signals`.
"""

import config


def combine_signals(model_score: float, style_score: float) -> float:
    """
    Combine two 0-1 signals into one 0-1 score. Higher means more likely AI.

    The rule: the signal that reads more human counts for
    `WEIGHT_MORE_HUMAN_SIGNAL` and the one that reads more AI for the rest:

        combined = w * min(model, style) + (1 - w) * max(model, style)

    In unit 7 `w` was 0.75, so the AI end had to be earned by both signals. The
    unit 8 attack run showed that let one cheaply fooled signal decide the
    whole score (EV01, EV09), so it is now 0.5, a plain average. With 0.5 the
    min/max form is the same as averaging; it stays in this shape so the weight
    in config.py is the only thing to change.

    The trade: more real writing now lands in "unsure" instead of "human" (the
    attack set's FP01, FP06 and PI06), in return for fewer evasions getting a
    human label.

    What it cannot fix: a writer both signals misread. Plain, even prose scores
    high on both, so there is no disagreement to lean on.
    """
    low, high = sorted((model_score, style_score))
    w = config.WEIGHT_MORE_HUMAN_SIGNAL
    return round(w * low + (1 - w) * high, 4)


LABELS = {
    "human": "We think this was probably written by a person.",
    "unsure": (
        "We can't tell whether this was written by a person or with an AI "
        "tool. Our checks aren't reliable enough to say, so please don't read "
        "this as a judgment about your work. If it doesn't look right to you, "
        "you can appeal using your submission ID."
    ),
    "ai": (
        "This may have been written with an AI tool. Checks like ours often "
        "get plain, simply written text wrong, so this is not a finding. If "
        "you wrote it yourself, you can appeal using your submission ID and "
        "ask for a review."
    ),
}


def score_to_label(score: float) -> tuple[str, str]:
    """
    Turn a score into a guess and the text a reader actually sees.

    Returns (guess, label_text): `guess` is "human" / "unsure" / "ai" and
    `label_text` is the sentence shown to a person. The label never shows a
    number and never says "confidence", and the two non-human labels say they
    can be wrong and point at the appeal. The wording is in `LABELS`; the
    reasoning is in the README under "Label Variants".

    The score ranges are `config.HUMAN_THRESHOLD` and `config.AI_THRESHOLD`.
    """
    if score >= config.AI_THRESHOLD:
        return "ai", LABELS["ai"]
    if score <= config.HUMAN_THRESHOLD:
        return "human", LABELS["human"]
    return "unsure", LABELS["unsure"]


def label_ranges() -> list[tuple[str, str]]:
    """
    The score range each label covers. Your README needs these beside the
    label text — given to you so the numbers can't drift apart from config.py.
    """
    return [
        ("high-confidence human", f"0.00 – {config.HUMAN_THRESHOLD:.2f}"),
        ("unsure", f"{config.HUMAN_THRESHOLD:.2f} – {config.AI_THRESHOLD:.2f}"),
        ("high-confidence AI", f"{config.AI_THRESHOLD:.2f} – 1.00"),
    ]
