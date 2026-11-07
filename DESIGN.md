# Milestone 1 — Trace a submission before you build one

Working notes, written before any code. Nothing here is measured yet: every score
below is an **expectation** that Milestone 4's calibration inputs either confirm
or break. Pieces of this get lifted into the README's *What This Does* and
*Signals and Scoring* sections.

---

## 1. The path a submission takes

```
 writer ──► route ──► signal one ──► signal two ──► combine ──► label ──► log ──► response
```

| # | Thing it passes through | Where it lives | What it adds |
|---|---|---|---|
| 1 | **The route** | `app.py::submit` | Checks the request is usable (JSON object, `text` is a non-empty string of sensible length, `creator_id` present). Mints a `content_id`. A bad request stops here with a 400 and never reaches a signal. |
| 2 | **Signal one — the model signal** | `detector.py::model_signal` | `model_score` (0–1, higher = more AI-like): how predictable gpt2 finds the text. |
| 3 | **Signal two — the style signal** | `stylometry.py::style_signal` | `style_score` (0–1, same direction): how even and repetitive the shape of the text is. |
| 4 | **The combining rule** | `scoring.py::combine_signals` | `combined_score` (0–1): one number from two, including what to do when they disagree. |
| 5 | **The label mapping** | `scoring.py::score_to_label` | `guess` (`human` / `unsure` / `ai`) and the sentence a person reads. This is where a number turns into words. |
| 6 | **The audit log** | `audit.py::log_decision` | A permanent record: all nine fields, `status: decided`. Written *before* we reply, so a crash while answering can't lose the decision. |
| 7 | **The response** | `app.py::submit` | JSON back to the caller: `content_id` (the handle for appeals), the label, both signal scores. |

The appeal is a second, separate path: `POST /appeal` → check `content_id` exists
(`audit.entries_for`) → `audit.log_appeal` (status becomes `under_review`) →
confirm to the writer.

The seams worth watching: step 1→2 (a bad input must never become a 500 from
inside the model), 2/3→4 (both signals must point the same way), and 5→7 (the
label text is the only thing the writer sees, so it carries the whole burden).

---

## 2. The two signals

### Signal one — `detector.py` (given): predictability to a language model

- **What it measures:** perplexity under gpt2 on the first ~400 tokens — how
  surprised a model is by each next word — squashed to 0–1 (low perplexity →
  high AI score).
- **Why it might differ:** a model writes by picking likely next words, so its
  output is text a model finds easy to predict. Human writing wanders: odd word
  choices, abrupt turns, specifics.
- **What it can't see:**
  - **Authorship.** Predictable is not the same as machine-written. It rewards
    *common words in short, ordinary sentences*, and plenty of real people write
    like that: second-language writers sticking to vocabulary they're sure of,
    younger writers, anyone being plain on purpose.
  - The reverse: dense, ornate prose full of rare words reads as human, so an
    AI asked to write fancy gets through.
  - Anything past ~300 words (it truncates), so text can be appended after the
    part that gets read.
  - gpt2 is old; modern model output isn't what it was tuned against. Text it
    has memorised (famous quotes, boilerplate) scores as maximally predictable.

### Signal two — `stylometry.py` (mine): the shape of the text

- **What it measures:** sentence-length spread (stdev ÷ mean), type-token ratio
  (unique words ÷ total words), and punctuation density/variety (semicolons and
  dashes weigh more than full stops), each scaled and flipped so higher = more
  AI-like, then combined.
- **Why it might differ:** "most likely next word" produces even, mid-length
  sentences and a narrower vocabulary. Human prose is lumpier — a three-word
  sentence beside a forty-word one.
- **What it can't see:**
  - **Meaning.** It can't read, so anything that changes the shape without
    changing the substance moves it: sprinkling typos, chopping sentences,
    pasting in a quotation. All cheap and deliberate.
  - Short texts give unstable numbers (one-sentence input has no spread at all),
    and type-token ratio falls as text gets longer, so length alone can fake a
    signal.
  - Any human who happens to write in even, plain sentences.

### The uncomfortable overlap

Both blind spots are aimed at **the same writer**. Plain, short, common-word
prose reads as AI to signal one *and* as AI to signal two (even sentences,
repeated vocabulary). So the two signals are not independent witnesses for this
person: they agree, and they're both wrong. Averaging doesn't rescue them. That
shapes the false-positive trace below.

---

## 3. Tracing the false positive

**The person.** A ninth-grader writing in their second language submits a
150-word reflection they wrote themselves. Short sentences, vocabulary they
trust, little punctuation beyond full stops.

**What they got (expected, to verify in Milestone 4):**

| Stage | Result | Why |
|---|---|---|
| Route | accepted | valid input |
| `model_score` | high (≈ 0.8+) | common words, ordinary sentences → gpt2 isn't surprised |
| `style_score` | high | even sentence lengths, narrow vocabulary, almost no varied punctuation |
| `combined_score` | high | both signals agree — nothing to average away |
| Label | **high-confidence AI** | above `AI_THRESHOLD` |

**What the label said to them.** With placeholder wording this would be
"high-confidence AI", an accusation with no evidence behind it that this person
can check. The wording I want instead for that tier:

> "This looks like it may have been written with an AI tool. Detectors like this
> one often get plain, simply-written text wrong, so this is not a finding. If
> you wrote it yourself, you can ask for a review."

It must (a) say it can be wrong, (b) say it's not a ruling, (c) point at the
appeal, and (d) never show a number or the word "confidence".

**What they can do about it.** `POST /appeal` with the `content_id` from their
response and a sentence or two of reasoning. The log records it beside the
original decision and marks it `under_review`.

**The gaps this exposes:**

1. The appeal path **records** but doesn't **re-check**; the spec says no
   automatic re-checking. So an appeal currently ends in a log line nobody is
   obliged to read. The confirmation message must not promise a human will
   review it unless one will. I should say plainly what happens.
2. The person needs the `content_id`. It's in the response, but a client that
   throws away the body strands them. The label text should be shown with the
   id, not instead of it.
3. This writer has the least room to argue back (the structural point in
   `detector.py`), and the thing deciding whether they're accused at all is a
   threshold.

**What this decides.** Falsely accusing a real writer is the costly error;
letting some AI text through is the cheap one. So:

- Make the **AI label hard to reach**: a high `AI_THRESHOLD` (leaning ≈ 0.8, not
  the 0.65 placeholder) and a wide `unsure` band.
- In the combining rule, lean toward the signal that reads *more human* when
  they split, and don't let one signal alone push a score into AI territory.
- Accept the trade: some AI text will land in `unsure`. That's the price, and
  it's paid by the platform, not by the writer.

Milestone 4 is where the real numbers confirm or overturn all of this: run a
plainly-written human paragraph through both signals and see where it lands.

---

## 4. The two endpoint contracts

All bodies are JSON. All errors share one shape so a client handles them once:

```json
{"error": "machine_readable_code", "message": "A sentence a person could read."}
```

### `POST /submit`

**In**

| Field | Type | Required | Rules |
|---|---|---|---|
| `text` | string | yes | Not blank after trimming. At least 20 words (below that the signals aren't meaningful). At most 20,000 characters. Only the first ~400 tokens are scored, whatever is sent. |
| `creator_id` | string | yes | Non-blank, at most 100 characters. Opaque to us: whatever the caller uses to identify the writer. Not authenticated. |

**Out — `200`**

| Field | Type | Meaning |
|---|---|---|
| `content_id` | string | A fresh UUID4 for this submission. The handle `/appeal` needs. |
| `guess` | `"human"` \| `"unsure"` \| `"ai"` | Machine-readable verdict. |
| `confidence` | number 0–1 | How far from a coin flip, `2·\|combined_score − 0.5\|`. Low for `unsure` by construction. **Not** the probability of AI. |
| `label` | string | The full sentence a person reads. Contains no numbers. |
| `model_score` | number 0–1 | Signal one. Higher = more AI-like. |
| `style_score` | number 0–1 | Signal two. Higher = more AI-like. |
| `combined_score` | number 0–1 | After `combine_signals`. Higher = more AI-like. This is the number the thresholds apply to. |

**Out — errors**

| Status | `error` | When |
|---|---|---|
| 400 | `invalid_json` | Body isn't a JSON object. |
| 400 | `missing_field` | `text` or `creator_id` absent, null, or not a string. |
| 400 | `empty_text` | `text` is blank. |
| 400 | `text_too_short` | Under 20 words. |
| 413 | `text_too_long` | Over 20,000 characters. |
| 429 | `rate_limited` | Unit 8. Shape already defined in `app.py`. |
| 503 | `detector_unavailable` | The model couldn't load (`DetectorUnavailable`). |

Every outcome — decision *or* rejected input — leaves an audit entry.

### `POST /appeal`

**In**

| Field | Type | Required | Rules |
|---|---|---|---|
| `content_id` | string | yes | Must match a logged decision. |
| `reasoning` | string | yes | Non-blank, at most 2,000 characters. Why the writer says the label is wrong. |

**Out — `200`**

| Field | Type | Meaning |
|---|---|---|
| `content_id` | string | Echoed back. |
| `status` | `"under_review"` | The item's new status. |
| `message` | string | Plain confirmation that the appeal was recorded. Says what happens next only as far as that's true. |

**Out — errors**

| Status | `error` | When |
|---|---|---|
| 400 | `invalid_json` / `missing_field` / `empty_reasoning` | As above. |
| 404 | `unknown_content_id` | No decision logged under that id — covers typos, which are the usual failure. |

Appealing the same `content_id` twice appends a second entry and returns the
same `200`. The log is append-only, so nothing is overwritten.

---

## 5. Read-back: could someone build against this without asking me?

Questions I'd have asked if I were the other person, and the answers now written
above:

- *What does `confidence` mean, and does 0.9 on `human` mean the same as 0.9 on
  `ai`?* Yes — distance from a coin flip. `combined_score` carries direction.
- *Which way do scores point?* Higher = more AI-like, everywhere.
- *What's "too short"?* 20 words. *Too long?* 20,000 characters, and only the
  start is scored anyway.
- *What does a missing `creator_id` do?* 400. It's required.
- *What do I get if I typo the `content_id`?* 404, not a silent success.

Still open, and mine to decide before Milestone 3 rather than guess at:

- Whether 20 words is the right floor. It's a guess until I see how unstable
  the style signal is on short text.
- Whether an appeal should be refused for a `human`-labelled item. Currently no:
  anyone can appeal anything they hold the id for.
- `creator_id` isn't authenticated, so anyone who learns a `content_id` can
  appeal it. Acceptable for this project; worth a sentence in the README.
