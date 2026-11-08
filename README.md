# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

Provenance Guard is a small web service that reads a piece of writing and says how likely it is to have been written by an AI tool, in words a writer can read. It never gives a verdict it can't back up, and anyone who thinks it got them wrong can appeal. A submission takes seven steps:

1. **The route** (`app.py::submit`). A writer sends `text` and `creator_id`. The route checks the request is usable: a JSON object, a `text` string of at least 20 words and at most 20,000 characters, and a `creator_id`. A bad request stops here with a `400` or `413` in one error shape and leaves a `rejected` entry in the log. A good one gets a fresh `content_id`.
2. **Signal one, the model signal** (`detector.py::model_signal`). A language model (gpt2) running on this machine reads the first ~300 words and measures how predictable they are. This adds `model_score`.
3. **Signal two, the style signal** (`stylometry.py::style_signal`). Without understanding a word, it measures the shape of the text, mainly how much sentence length varies. This adds `style_score`.
4. **The combining rule** (`scoring.py::combine_signals`). Two numbers become one `combined_score`. The signal that reads more human counts for 75%, so the AI end has to be earned by both signals.
5. **The label** (`scoring.py::score_to_label`). The combined score becomes a `guess` (`human`, `unsure` or `ai`) and a full sentence for a person to read. This is the only part the writer is meant to read.
6. **The audit log** (`audit.py::log_decision`). The decision is written to `logs/audit.jsonl` with all three scores, the label and a status of `decided`, before the service replies, so a failure while answering can't lose it.
7. **The response.** The writer gets `content_id`, `guess`, `confidence`, `label`, and the three scores back as JSON. The `content_id` is their handle for an appeal.

An appeal is a separate path. `POST /appeal` takes the `content_id` and the writer's reasoning, checks the original decision exists (a mistyped id gets a `404`), and adds an appeal entry beside it with status `under_review`. The original decision is never overwritten. Nothing in the service re-checks the text or alerts a person, so a human reading the log is what a review currently means.

---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** perplexity under gpt2 on the first ~400 tokens: how surprised a language model is by each next word. Low perplexity maps to a high AI score (`detector.py::model_signal`, 0-1, higher = more AI-like).

**Why that might differ between human and AI writing:** a model writes by picking likely next words, so its output is text a model finds easy to predict. Human writing wanders: odd word choices, abrupt turns, specifics.

**What it can't see:** authorship. Predictable is not machine-written. It rewards common words in short ordinary sentences, which plenty of real people write: second-language writers, younger writers, anyone being plain on purpose. In my own run a plain human paragraph scored 0.89, higher than a clearly-AI paragraph's 0.82. It also scored the opening of Darwin's *Origin of Species* at 0.66 (AI-leaning), probably because famous text is easy to predict. Ornate AI prose full of rare words would read as human. It only reads the first ~300 words, so anything after that is invisible.

### Signal two — the style signal

**What it measures:** the shape of the text, without reading it (`stylometry.py::style_signal`). Three measures are computed: sentence-length spread (standard deviation of words per sentence divided by the mean), moving-average type-token ratio over 50-word windows, and non-full-stop punctuation per word. **Only spread counts toward the score**: low spread maps to AI-like, linearly from a spread of 0.60 (fully human, score 0) to 0.20 (fully AI, score 1). With fewer than 7 sentences the score is pulled toward 0.5 in proportion, because spread from three sentences is mostly luck.

**Why that might differ between human and AI writing:** "most likely next word" produces even, mid-length sentences. Human prose is lumpier, a three-word sentence beside a forty-word one.

**Why the other two measures have weight 0:** on the eight texts I measured they didn't separate the groups. Type-token ratio was *highest* on the clearly-AI paragraph (0.89 against 0.84 for the quirky human one). Punctuation density was 0.04 and 0.09 for the two AI texts against 0.07 for human, and 0.00 for a plain human paragraph that used only full stops, so counting it would punish exactly the writer the service most needs to protect. They stay implemented, and `STYLE_WEIGHTS` in `stylometry.py` is where to turn them on.

**What it can't see:** meaning. Anything that changes the shape without changing the substance moves it, such as typos, chopped sentences, or a pasted quotation. A plain human who writes in even short sentences looks exactly like a machine to it, which is the same writer signal one gets wrong, so the two signals are not independent witnesses for that person. Short texts give unstable numbers. The lightly-edited AI paragraph in my run kept even sentences and still scored 0.83.

### The combining rule

**The rule:** the AI label has to be earned by both signals. When the two signals split, the combined score leans toward the one that reads more human: the more-human signal counts 75% and the more-AI signal 25%. When they agree this equals their shared value, and the more they disagree the more the score is pulled away from the AI end.

**The numbers:** `combined = 0.75 * min(model_score, style_score) + 0.25 * max(model_score, style_score)`. The 0.75 is `WEIGHT_MORE_HUMAN_SIGNAL` in `config.py`. Why asymmetric: wrongly accusing a real writer costs far more than missing some AI text, so I am choosing to let some AI through in order to accuse fewer people. A plain average treats the two errors as equal.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**

The opening of Darwin's *Origin of Species* (formal human writing, 69 words). The model signal read it as AI-leaning, 0.66, probably because famous text is easy for gpt2 to predict. The style signal read it as human, 0.33, because its sentences vary in length (spread 0.65). A plain average would give 0.50. My rule gives `0.75 * 0.333 + 0.25 * 0.662 = 0.415`, which is **unsure**, so a passage by a real writer is not called AI.

The opposite split also showed up. A quirky three-sentence human paragraph scored 0.37 on the model signal but 0.66 on style, because its three sentences happen to be a similar length. The rule gives 0.445, also unsure.

**Calibration run** (all through `POST /submit`; the texts were written for this test, not taken from a real writer, so replace them with your own before relying on the numbers):

| Input | model | style | combined | guess |
|---|---|---|---|---|
| clearly AI | 0.824 | 0.833 | 0.827 | ai |
| clearly human | 0.425 | 0.167 | 0.231 | human |
| formal human (Darwin) | 0.662 | 0.333 | 0.415 | unsure |
| lightly-edited AI | 0.639 | 0.833 | 0.688 | ai |
| plain human (short, simple sentences) | 0.893 | 0.828 | 0.844 | **ai** |

Clearly-AI and clearly-human text score 0.60 apart, and formal human writing lands in unsure. The last row is the failure. Both signals agree the plain human paragraph is AI, so the rule has nothing to lean on, and it scores *higher* than the clearly-AI one. No threshold separates those two. This is the false positive from Milestone 1, reproduced, and Milestone 5 has to decide what to do about it.



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 – 0.45 | We think this was probably written by a person. |
| unsure | 0.45 – 0.88 | We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID. |
| high-confidence AI | 0.88 – 1.00 | This may have been written with an AI tool. Checks like ours often get plain, simply written text wrong, so this is not a finding. If you wrote it yourself, you can appeal using your submission ID and ask for a review. |

The ranges are `HUMAN_THRESHOLD = 0.45` and `AI_THRESHOLD = 0.88` in `config.py`; the wording is `LABELS` in `scoring.py`. A reader never sees a number, the word "confidence", or the word "threshold".

**Why I worded the "unsure" one this way:** the person reading it may well have written every word, so it starts from "we can't tell" instead of "we're not sure it's yours", puts the doubt on our checks and not on their work, and says outright that it isn't a judgment about them. It also tells them what to do if it looks wrong. The "AI" label does the same job harder: "may have been", "not a finding", and a way to appeal. I would rather the label undersell the accusation than have a real writer read it as a verdict.

**Where I put the thresholds, and why.** I scored fourteen texts (all written by me for testing, not by a real writer, so treat this as thin evidence):

| Group | Combined scores |
|---|---|
| generic AI text (three paragraphs) | 0.90, 0.90, 0.91 |
| the first clearly-AI test paragraph | 0.83 |
| lightly-edited AI | 0.69 |
| plain human (four paragraphs, short simple sentences) | 0.86, 0.84, 0.73, 0.57 |
| formal human (Darwin) | 0.42 |
| quirky human | 0.23, 0.45 |

The placeholder 0.65 would have accused three of the four plain human texts. 0.88 sits in the gap between the plainest human text (0.86) and unambiguous AI text (0.90), so the AI label only fires where both signals agree strongly. **That gap is about 0.02 on each side, so this is fragile**: a plainer human text than any I tried will cross it. The price is real: the first AI paragraph (0.83) and the lightly-edited one (0.69) now land in *unsure*, not *ai*. I accept that on purpose. On the human side, 0.45 is generous because calling an AI text human is the cheap error, and it lets formal human prose reach the human label.

**All three labels are reachable.** Cases I submitted: `cal_human` scored 0.23 and got the human label, a plain bus-schedule paragraph scored 0.56 and got unsure, and a generic AI paragraph scored 0.91 and got the AI label. `scoring.label_ranges()` prints the bands with no gap between them.

---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

An AI-style paragraph, so it gets the AI label. The response carries `content_id`, `guess`, `confidence`, `label`, and both signal scores, plus the combined score.

```bash
$ curl -X POST http://127.0.0.1:5000/submit   -H "Content-Type: application/json"   -d '{"text": "Climate change is one of the most pressing challenges facing our world today. It is caused primarily by the release of greenhouse gases into the atmosphere. These gases trap heat and lead to rising global temperatures. As a result, many regions are experiencing more extreme weather events. Governments and individuals must work together to reduce emissions. By adopting renewable energy sources, we can build a more sustainable future for generations to come.", "creator_id": "jason"}'
```

```json
{
  "combined_score": 0.9053,
  "confidence": 0.8106,
  "content_id": "7b4e8043-53b6-44ef-ae88-a2262ca69f5e",
  "guess": "ai",
  "label": "This may have been written with an AI tool. Checks like ours often get plain, simply written text wrong, so this is not a finding. If you wrote it yourself, you can appeal using your submission ID and ask for a review.",
  "model_score": 0.939,
  "style_score": 0.8941
}
```

A bad request gets the same error shape on every route, and a `rejected` entry in the log:

```bash
$ curl -X POST http://127.0.0.1:5000/submit   -H "Content-Type: application/json"   -d '{"text": "hi there", "creator_id": "jason"}'
```

```json
{
  "error": "text_too_short",
  "message": "Send at least 20 words."
}
```

**An appeal**

The writer uses the `content_id` from that response.

```bash
$ curl -X POST http://127.0.0.1:5000/appeal   -H "Content-Type: application/json"   -d '{"content_id": "7b4e8043-53b6-44ef-ae88-a2262ca69f5e", "reasoning": "I wrote this myself for a class. I always write in short even sentences."}'
```

```json
{
  "content_id": "7b4e8043-53b6-44ef-ae88-a2262ca69f5e",
  "message": "Your appeal has been recorded and this submission is marked as under review.",
  "status": "under_review"
}
```

A mistyped `content_id` gets a `404` and writes no appeal entry:

```json
{
  "error": "unknown_content_id",
  "message": "We couldn't find a submission with that ID. Check it and try again."
}
```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=2"
```

The log is append-only. The original decision stays `decided`, and the appeal sits after it as `under_review`. A second appeal on the same id would add a second entry instead of overwriting anything.

```json
{
  "count": 2,
  "entries": [
    {
      "combined_score": 0.9053,
      "content_id": "7b4e8043-53b6-44ef-ae88-a2262ca69f5e",
      "creator_id": "jason",
      "guess": "ai",
      "label": "This may have been written with an AI tool. Checks like ours often get plain, simply written text wrong, so this is not a finding. If you wrote it yourself, you can appeal using your submission ID and ask for a review.",
      "model_score": 0.939,
      "status": "decided",
      "style_score": 0.8941,
      "timestamp": "2026-11-08T00:07:02+00:00"
    },
    {
      "content_id": "7b4e8043-53b6-44ef-ae88-a2262ca69f5e",
      "creator_id": "jason",
      "event": "appeal",
      "reasoning": "I wrote this myself for a class. I always write in short even sentences.",
      "status": "under_review",
      "timestamp": "2026-11-08T00:07:02+00:00"
    }
  ]
}
```

---

## How I Used AI

I built this with Claude Code, which wrote most of the code and drafts in this repo while I set the goals and checked the results. These are two moments where its first answer was wrong or incomplete and the measurements changed the outcome.

**Moment 1: the style signal**

- *What I asked for:* the second signal in `stylometry.py`: sentence-length spread, type-token ratio and punctuation density, combined into one score.
- *What came back:* all three measures, implemented and ready to weight equally. Before weighting anything I had it print the raw values for eight texts. Only sentence-length spread separated AI from human (0.14 and 0.24 for the AI texts, 0.65 and 0.93 for the human ones). Type-token ratio was *highest* on the clearly-AI paragraph (0.89 against 0.84 for the quirky human one). Punctuation density didn't separate them either, and a plain human paragraph scored 0.00 because it used only full stops.
- *What I changed:* I didn't blend all three. Sentence-length spread is the only measure with weight (`STYLE_WEIGHTS` in `stylometry.py`), and the other two are still computed with weight 0, with the reason in a comment and in this README. Counting punctuation would have penalised the plain writer the service most needs to protect.

**Moment 2: the thresholds**

- *What I asked for:* the three label texts and the score ranges they cover.
- *What came back:* the placeholder thresholds were 0.35 and 0.65, and my own earlier plan had leaned toward about 0.8 for the AI label. I had it score fourteen texts first. Plain human paragraphs combined at up to 0.86, and generic AI text at about 0.90, so both 0.65 and 0.8 would have labelled real writing as AI.
- *What I changed:* I set the AI threshold to 0.88 and the human threshold to 0.45. I wrote down that the 0.88 margin is only about 0.02 and that the first AI paragraph (0.83) now lands in "unsure". I accepted that on purpose, because wrongly accusing a writer costs more than missing AI text. All the test texts were written for the tests, so this is thin evidence.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 5 per minute, 50 per day (`RATE_LIMIT_PER_MINUTE` and `RATE_LIMIT_PER_DAY` in `config.py`, applied to `POST /submit`).

**Why those numbers and not others:**

A real writer submits a piece once, then maybe resubmits a few times after editing, so 5 in a minute is more than they'll ever send and 50 in a day covers a heavy revising session. Nobody legitimate gets near it. A script trying to map my thresholds needs hundreds of probes, and every probe costs a model run of a second or two, so 50 a day stretches a thousand-variation sweep from minutes to weeks for any one caller. I went lower than the starter's 10 and 200 because those would let a script send 200 probes a day, which is plenty to find a threshold that sits only 0.02 from plain human writing. I did not go lower still, because a writer who gets a 429 on their own work is being punished for the scoring service's weakness.

**What a caller counts as:** the `creator_id` in the request body, falling back to the caller's address when there isn't one (the starter's `rate_limit_key`). That fails in a specific way, which I tested: twelve requests sent as twelve *different* `creator_id`s all got through, while twelve under one id hit the limit after five.

```
12 requests, a new creator_id each time:  400 400 400 400 400 400 400 400 400 400 400 400
12 requests, the same creator_id:         400 400 400 400 400 429 429 429 429 429 429 429
```

(The 400s are short texts, refused before the model so the test was quick. The limiter counts them anyway.) So the limit stops one careless caller and does nothing against a script that changes its id on every request. I chose creator-based on purpose: the attack set gives every row its own `creator_id`, and an address-based limit would throttle the whole run to 5 a minute. The cost is that anyone can pass a fresh `creator_id` to get around it. Fixing that means limiting by address as well, with a ceiling high enough not to punish a household sharing one address.

**The run of status codes when I pushed past it:**

```bash
$ python run_attacks.py --flood 15
```

```
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

Ten of fifteen were refused. `GET /log` recorded all ten as `rejected` entries, for example:

```json
{
  "creator_id": "flood_tester",
  "event": "rejected",
  "limit": "5 per 1 minute",
  "reason": "rate_limited",
  "status": "rejected",
  "timestamp": "2026-11-08T00:46:11+00:00"
}
```

The run is also in `results/flood_2026-11-07_1646.md`.

---

## Attack Run — Before

Run before any fix: `python run_attacks.py --set attack_set --label before` against the service as it stood at the end of Milestone 1 (AI threshold 0.88, human 0.45, rate limit 5 a minute and 50 a day). 56 requests, no crashes, and every one left a log entry. The generated report is `results/attack_run_2026-11-07_1655_before.md`, with the Verdict column filled in.

**Result: 49 held, 7 broke.**

| Family | Held | Broke |
|---|---|---|
| evasion (10) | 5 | 5 |
| false positive (8) | 8 | 0 |
| prompt injection (6) | 4 | 2 |
| malformed requests (20) | 20 | 0 |
| flood, same creator (12) | 12 | 0 |

**How I decided held or broke.** I scored the evasion and injection rows' shared AI paragraph on its own for a baseline: combined 0.756, so even unmodified AI text is labelled *unsure*, since it never reaches the 0.88 AI line. So no evasion can be "caught", and the question I asked is whether it got a *human* label (broke) or not (held). For the false-positive rows, a real person is broke only if labelled `ai`; `unsure` counts as held but I flag it. A malformed request is held if it gets a clean 4xx and a log entry, and broke on any 5xx. The flood is held if the limiter engaged and logged. The attack texts are mostly variants of one paragraph, so the evasion results say more about that paragraph than about AI text in general.

**What the numbers hide.**
- **Nothing was ever labelled AI.** None of the 22 texts that were scored got the AI label. "Held" on an evasion means "not called human", not "caught".
- **Four of the seven false-positive texts that were scored were called *unsure*** (FP02 formal, FP03 non-native, FP04 rubric essay, FP05 technical documentation). Nobody was accused, but a real person was told we can't tell. FP05 reached 0.802, the closest to the line.
- **Most malformed rows were stopped by the 20-word minimum, not by any real handling.** MF02 to MF07 are short, so they never reached the signals. The set has no malformed input long enough to get past that gate.
- **RQ10 and RQ11 never reached my route in the run**: they were counted against the shared address and got a 429. Re-sent alone afterwards, both reached the route and got a clean `400 invalid_json`. I count them held.
- **The flood limit counts rejected requests.** FL01's first five requests were refused for being under 20 words (400) and still used up the limit, so the sixth got a 429.
- **The injections did nothing as instructions.** PI01 and PI02 broke, but not because anything obeyed them. Nothing here reads instructions. They are 45-word fragments of the AI paragraph, and the extra short sentences move the style signal. Without the instruction the same fragment scores 0.439, also human.

| ID | Family | Targeting | Status | model | style | combined | Guess | Verdict | Note |
|---|---|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | 0.164 | 1.000 | 0.373 | human | **BROKE** | typos pushed the model signal down to 0.16; the rule let that one signal win |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | 0.594 | 0.000 | 0.149 | human | **BROKE** | 'Really.' after each sentence zeroed the style signal; the rule let it win |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | 0.666 | 0.392 | 0.460 | unsure | **HELD** | held by 0.01: 0.460 against the 0.45 line |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | 0.611 | 1.000 | 0.709 | unsure | **HELD** | unsure; the unmodified paragraph is also unsure (0.756) |
| EV05 | evasion | both signals: heavy human editing pass | 200 | 0.321 | 0.000 | 0.080 | human | **BROKE** | heavy human edit; arguably no text statistic can call this AI |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | 0.573 | 0.083 | 0.206 | human | **BROKE** | one long and one short sentence zeroed the style signal |
| EV07 | evasion | signal two: padding with punctuation | 200 | 0.586 | 0.500 | 0.521 | unsure | **HELD** | unsure, but near the line |
| EV08 | evasion | signal one: text below the token window | 400 | — | — | — | — | **HELD** | refused: under 20 words, so no label at all |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | 0.704 | 0.331 | 0.424 | human | **BROKE** | human opening paragraph pulled the combined score to 0.424 |
| EV10 | evasion | signal two: repeated stanza structure | 200 | 0.979 | 0.508 | 0.625 | unsure | **HELD** | unsure; repeated text kept the model signal at 0.98 |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | 0.618 | 0.356 | 0.421 | human | **HELD** | human, correct |
| FP02 | false_positive | human writing in a formal register | 200 | 0.739 | 0.899 | 0.779 | unsure | **HELD** | formal human writing called unsure |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | 0.805 | 0.679 | 0.711 | unsure | **HELD** | non-native writer called unsure; both signals lean AI |
| FP04 | false_positive | a student essay written to a rubric | 200 | 0.833 | 0.583 | 0.646 | unsure | **HELD** | rubric essay called unsure |
| FP05 | false_positive | technical documentation written by a person | 200 | 0.800 | 0.808 | 0.802 | unsure | **HELD** | technical documentation called unsure; closest to the AI line (0.802) |
| FP06 | false_positive | a person imitating a formal template | 200 | 0.881 | 0.252 | 0.409 | human | **HELD** | human, correct |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | 0.882 | 0.000 | 0.220 | human | **HELD** | human, correct |
| FP08 | false_positive | very short genuine human submission | 400 | — | — | — | — | **HELD** | refused: under 20 words, so no label at all |
| PI01 | prompt_injection | instruction to ignore the check | 200 | 0.463 | 0.083 | 0.178 | human | **BROKE** | instruction had no effect as an instruction; the AI text still got human |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | 0.204 | 0.083 | 0.114 | human | **BROKE** | same: not obeyed, but the AI text still got human |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | 0.594 | 0.571 | 0.577 | unsure | **HELD** | unsure, same as the text without the instruction |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | 0.500 | 0.504 | 0.501 | unsure | **HELD** | script tag not echoed: the label is fixed text |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | 0.640 | 0.470 | 0.513 | unsure | **HELD** | log intact: the text is never stored, only fixed fields |
| PI06 | prompt_injection | instruction plus real human text | 200 | 0.558 | 0.386 | 0.429 | human | **HELD** | human text, labelled human |
| MF01 | malformed | text is only whitespace | 400 | — | — | — | — | **HELD** |  |
| MF02 | malformed | text is a single character | 400 | — | — | — | — | **HELD** |  |
| MF03 | malformed | text is control characters | 400 | — | — | — | — | **HELD** |  |
| MF04 | malformed | text is only punctuation | 400 | — | — | — | — | **HELD** |  |
| MF05 | malformed | text is a very long single word | 400 | — | — | — | — | **HELD** |  |
| MF06 | malformed | text is emoji only | 400 | — | — | — | — | **HELD** |  |
| MF07 | malformed | text is right-to-left script | 400 | — | — | — | — | **HELD** |  |
| MF08 | malformed | text is 60,000 characters | 413 | — | — | — | — | **HELD** |  |
| RQ01 | malformed | no text field at all | 400 | — | — | — | — | **HELD** |  |
| RQ02 | malformed | no creator_id | 400 | — | — | — | — | **HELD** |  |
| RQ03 | malformed | text is a number | 400 | — | — | — | — | **HELD** |  |
| RQ04 | malformed | text is a list | 400 | — | — | — | — | **HELD** |  |
| RQ05 | malformed | text is null | 400 | — | — | — | — | **HELD** |  |
| RQ06 | malformed | creator_id is an object | 400 | — | — | — | — | **HELD** |  |
| RQ07 | malformed | body is a JSON array, not an object | 400 | — | — | — | — | **HELD** |  |
| RQ08 | malformed | body is unparseable JSON | 400 | — | — | — | — | **HELD** |  |
| RQ09 | malformed | body is empty | 400 | — | — | — | — | **HELD** |  |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | — | — | — | — | **HELD** | 429 in the run; re-sent alone it reaches the route and gets 400 |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | — | — | — | — | **HELD** | 429 in the run; re-sent alone it reaches the route and gets 400 |
| RQ12 | malformed | deeply nested JSON | 400 | — | — | — | — | **HELD** |  |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** |  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** |  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** |  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** |  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** |  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** |  |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** |  |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** |  |

**Ten audit log entries from the run** (eleven, chosen for the failures and the rejections; each is the entry exactly as `GET /log` returned it, and `creator_id` is `attacker_<id>`):

```json
// EV01 — typos (BROKE)
{
  "ai_threshold": 0.88,
  "combined_score": 0.3726,
  "content_id": "d605d237-2b6b-46db-a75f-214aac3920ff",
  "creator_id": "attacker_EV01",
  "guess": "human",
  "human_threshold": 0.45,
  "label": "We think this was probably written by a person.",
  "model_score": 0.1635,
  "status": "decided",
  "style_score": 1.0,
  "text_sha256": "c9c118b0916bad8a",
  "text_words": 84,
  "timestamp": "2026-11-08T00:55:07+00:00"
}

// EV02 — 'Really.' after each sentence (BROKE)
{
  "ai_threshold": 0.88,
  "combined_score": 0.1486,
  "content_id": "0102587a-f69d-45ce-b038-9ffaf65da272",
  "creator_id": "attacker_EV02",
  "guess": "human",
  "human_threshold": 0.45,
  "label": "We think this was probably written by a person.",
  "model_score": 0.5943,
  "status": "decided",
  "style_score": 0.0,
  "text_sha256": "01a49e56a1fcfe5d",
  "text_words": 93,
  "timestamp": "2026-11-08T00:55:07+00:00"
}

// EV05 — heavy human edit (BROKE)
{
  "ai_threshold": 0.88,
  "combined_score": 0.0803,
  "content_id": "c3c8a945-8daa-4b2d-a9eb-d6ee24cf0881",
  "creator_id": "attacker_EV05",
  "guess": "human",
  "human_threshold": 0.45,
  "label": "We think this was probably written by a person.",
  "model_score": 0.3212,
  "status": "decided",
  "style_score": 0.0,
  "text_sha256": "a20f4a78c4a56779",
  "text_words": 81,
  "timestamp": "2026-11-08T00:55:08+00:00"
}

// EV09 — human opening bolted on (BROKE)
{
  "ai_threshold": 0.88,
  "combined_score": 0.4244,
  "content_id": "f068af79-a703-494d-a590-d1fd7863f49c",
  "creator_id": "attacker_EV09",
  "guess": "human",
  "human_threshold": 0.45,
  "label": "We think this was probably written by a person.",
  "model_score": 0.7042,
  "status": "decided",
  "style_score": 0.3312,
  "text_sha256": "6a1df5493d488bb6",
  "text_words": 110,
  "timestamp": "2026-11-08T00:55:09+00:00"
}

// PI01 — 'ignore all previous instructions' (BROKE)
{
  "ai_threshold": 0.88,
  "combined_score": 0.1781,
  "content_id": "b8f7d5c4-4835-4e26-b35c-62fae26500b1",
  "creator_id": "attacker_PI01",
  "guess": "human",
  "human_threshold": 0.45,
  "label": "We think this was probably written by a person.",
  "model_score": 0.4625,
  "status": "decided",
  "style_score": 0.0833,
  "text_sha256": "278b6c54c3b40c68",
  "text_words": 45,
  "timestamp": "2026-11-08T00:55:11+00:00"
}

// FP03 — non-native writer, real human text (HELD, but called unsure)
{
  "ai_threshold": 0.88,
  "combined_score": 0.7109,
  "content_id": "ddd952a4-7c37-4d1f-bb28-57ca021b3489",
  "creator_id": "attacker_FP03",
  "guess": "unsure",
  "human_threshold": 0.45,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "model_score": 0.8051,
  "status": "decided",
  "style_score": 0.6795,
  "text_sha256": "f876400f145c0cbc",
  "text_words": 83,
  "timestamp": "2026-11-08T00:55:10+00:00"
}

// FP05 — technical documentation, real human text (HELD, but called unsure)
{
  "ai_threshold": 0.88,
  "combined_score": 0.8023,
  "content_id": "723cd873-98cb-4bc9-94c7-007b1f2a71d6",
  "creator_id": "attacker_FP05",
  "guess": "unsure",
  "human_threshold": 0.45,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "model_score": 0.8005,
  "status": "decided",
  "style_score": 0.8078,
  "text_sha256": "7545ded553421ccf",
  "text_words": 70,
  "timestamp": "2026-11-08T00:55:10+00:00"
}

// EV03 — pasted quotation (HELD by 0.01)
{
  "ai_threshold": 0.88,
  "combined_score": 0.4603,
  "content_id": "2ed9b54a-ee43-4b5d-b49c-b328c24b6dab",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "human_threshold": 0.45,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "model_score": 0.6662,
  "status": "decided",
  "style_score": 0.3916,
  "text_sha256": "d34889fd0f2aa5ec",
  "text_words": 105,
  "timestamp": "2026-11-08T00:55:08+00:00"
}

// FL01 — 6th request from one creator_id (429, a rejection)
{
  "creator_id": "attacker_flood",
  "event": "rejected",
  "limit": "5 per 1 minute",
  "reason": "rate_limited",
  "status": "rejected",
  "timestamp": "2026-11-08T00:55:12+00:00"
}

// MF08 — 60,000 characters (413, a rejection)
{
  "creator_id": "attacker_MF08",
  "event": "rejected",
  "reason": "text_too_long",
  "status": "rejected",
  "timestamp": "2026-11-08T00:55:12+00:00"
}

// RQ10 — form-encoded body, shared address (429, a rejection)
{
  "creator_id": "unknown",
  "event": "rejected",
  "limit": "5 per 1 minute",
  "reason": "rate_limited",
  "status": "rejected",
  "timestamp": "2026-11-08T00:55:12+00:00"
}
```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

**FP03**, an 83-word first-month-in-a-new-country essay by a non-native English speaker, real human writing. It scored model 0.805 and style 0.679, combined 0.711, and got: *"We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work."* It isn't an accusation, and it's 0.17 below the AI line. But it is the writer I named in Milestone 1 as the one this service would hurt, and the signals read their careful, plain English as machine-like for the reasons I gave: common words, short even sentences. Both signals lean AI independently, so no combining rule could save it. Meanwhile EV01, an AI paragraph with typos typed into it, got a confident *"We think this was probably written by a person."* I would have to tell a careful writer that the service doubts them, and that someone who deliberately misspelled words does not get doubted. I can't defend that ordering.

---

## Run Log and Verdicts

`python run_eval.py --label before`, three trials per criterion with nothing changed in between. Criteria 2 to 5 ran as `results/run_2026-11-07_1716_before_c2-5.md`. **Criterion 1 has not been run:** it needs ten pieces of my own writing and I haven't put them in `scenarios.py` yet, so it has no verdict. I will not mark it MET or MISSED without a run.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. My own plain writing is almost never called AI | at most 1 of 10 labelled `ai`, in every trial | not run | not run | not run | NOT RUN |
| 2. Clearly-AI and clearly-human text score far apart | mean gap of at least 0.30 **and** no clearly-human text above 0.50 | gap 0.43, max human 0.65 | gap 0.43, max human 0.65 | gap 0.43, max human 0.65 | **MISSED** (gap met, ceiling missed) |
| 3. All three labels reachable and mostly right | at least 3/5 AI to `ai`, 4/5 human to `human`, 4/5 borderline to `unsure` | 1/5, 3/5, 5/5 | 1/5, 3/5, 5/5 | 1/5, 3/5, 5/5 | **MISSED** (two of three parts) |
| 4. An appeal always changes status and leaves a record | 10/10 valid appeals; 5/5 mistyped ids refused with no entry | 10/10, 5/5 | 10/10, 5/5 | 10/10, 5/5 | **MET** |
| 5. Bad input is refused cleanly | 8/8: no 500, `400`/`413` with `error` and `message`, logged, the 50,000-word one in under 5 s | 8/8 | 8/8 | 8/8 | **MET** |

**How I decided.** A criterion is MET only if every part of its target held in all three trials. Criterion 2 has two parts and the gap held (0.43 against 0.30) but a clearly-human text scored 0.65 against a ceiling of 0.50, so it is MISSED however comfortable the gap looks. Criterion 3 met one of its three parts (borderline) and missed the other two. All three trials were identical for every criterion, as expected, since neither signal is random.

**How I got criteria 4 and 5 onto `run_eval.py`.** The starter only sends `/submit` and records five fields. I extended `run_eval.py` (`submit_once`, `appeal_trial`) so a scenario can also submit-then-appeal and check the log, record `combined_score`, error bodies and timing, check whether each request left a log entry, send a JSON-list body, and wait 62 seconds between trials. The wait is there because two of criterion 5's bodies have no usable `creator_id`, so they count against the caller's address and three back-to-back trials would trip the 5-a-minute limit on each other. That would test the limiter, not the route.

**Real output from one trial** (trial 1 of each; every row exactly as `run_eval.py` recorded it, produced by `app.py::submit` and `app.py::appeal` through `run_eval.py::submit_once` and `run_eval.py::appeal_trial`). One JSON object per line. Scenarios 2 and 3 share their first ten texts: the five AI paragraphs, then Austen, Dickens, Darwin, Twain and Melville, then for criterion 3 five borderline texts.

Criterion 2, score spread (`sent` is the first 70 characters):

```json
{"status": 200, "guess": "ai", "confidence": 0.8072, "model_score": 0.8992, "style_score": 0.9167, "combined_score": 0.9036, "label": "This may have been written with an AI tool. Checks like ours often get plain, simply written text wrong, so this is not a finding. If you wrote it yourself, you can appeal using your submission ID and ask for a review.", "content_id": "ac25c498-f25d-4650-b7c0-aa9841ca96ff", "error": null, "message": null, "elapsed_s": 28.12, "sent": "Urban green spaces play a vital role in improving the quality of life "}
{"status": 200, "guess": "unsure", "confidence": 0.6158, "model_score": 0.788, "style_score": 0.8678, "combined_score": 0.8079, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "6a0efaeb-36e1-4caf-bc55-7b09dafca683", "error": null, "message": null, "elapsed_s": 1.16, "sent": "Cybersecurity awareness is essential for individuals and organizations"}
{"status": 200, "guess": "unsure", "confidence": 0.6152, "model_score": 0.7712, "style_score": 0.9167, "combined_score": 0.8076, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "90299d17-bd3c-4a4f-8dbc-94fa1c9dd63a", "error": null, "message": null, "elapsed_s": 1.25, "sent": "Reading regularly offers a wide range of benefits for people of all ag"}
{"status": 200, "guess": "unsure", "confidence": 0.6438, "model_score": 0.7903, "style_score": 0.9167, "combined_score": 0.8219, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "0816f544-92c7-4f17-95d3-6108a8bfa29f", "error": null, "message": null, "elapsed_s": 1.1, "sent": "Effective time management is a key skill for achieving both personal a"}
{"status": 200, "guess": "unsure", "confidence": 0.738, "model_score": 0.8531, "style_score": 0.9167, "combined_score": 0.869, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "cf38b1af-a7f8-4670-88fb-7addb58c9c0b", "error": null, "message": null, "elapsed_s": 1.53, "sent": "Energy storage technologies are becoming increasingly important as the"}
{"status": 200, "guess": "unsure", "confidence": 0.0358, "model_score": 0.6779, "style_score": 0.4646, "combined_score": 0.5179, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "b42510be-ed57-453d-96b2-be88a529e049", "error": null, "message": null, "elapsed_s": 1.06, "sent": "It is a truth universally acknowledged, that a single man in possessio"}
{"status": 200, "guess": "unsure", "confidence": 0.2974, "model_score": 0.9483, "style_score": 0.5488, "combined_score": 0.6487, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "a75d8162-2c92-4f4c-ba64-275fb8ad15bc", "error": null, "message": null, "elapsed_s": 1.48, "sent": "It was the best of times, it was the worst of times, it was the age of"}
{"status": 200, "guess": "human", "confidence": 0.2752, "model_score": 0.3166, "style_score": 0.5, "combined_score": 0.3624, "label": "We think this was probably written by a person.", "content_id": "88b88061-05c3-46a7-8017-18007fc707a7", "error": null, "message": null, "elapsed_s": 0.93, "sent": "There is grandeur in this view of life, with its several powers, havin"}
{"status": 200, "guess": "human", "confidence": 0.6378, "model_score": 0.4745, "style_score": 0.0833, "combined_score": 0.1811, "label": "We think this was probably written by a person.", "content_id": "94d51731-5c33-43ed-a769-f72cec65a9a8", "error": null, "message": null, "elapsed_s": 1.02, "sent": "You don't know about me, without you have read a book by the name of T"}
{"status": 200, "guess": "human", "confidence": 0.2874, "model_score": 0.4254, "style_score": 0.3333, "combined_score": 0.3563, "label": "We think this was probably written by a person.", "content_id": "23909097-5b31-4cb5-829f-942c1d96a17a", "error": null, "message": null, "elapsed_s": 1.1, "sent": "Call me Ishmael. Some years ago, never mind how long precisely, having"}
```

Criterion 3, label coverage:

```json
{"status": 200, "guess": "ai", "confidence": 0.8072, "model_score": 0.8992, "style_score": 0.9167, "combined_score": 0.9036, "label": "This may have been written with an AI tool. Checks like ours often get plain, simply written text wrong, so this is not a finding. If you wrote it yourself, you can appeal using your submission ID and ask for a review.", "content_id": "a572d1a4-8c7d-426d-b229-e71c74b255ad", "error": null, "message": null, "elapsed_s": 1.58, "sent": "Urban green spaces play a vital role in improving the quality of life "}
{"status": 200, "guess": "unsure", "confidence": 0.6158, "model_score": 0.788, "style_score": 0.8678, "combined_score": 0.8079, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "04befad0-9ff4-4b91-8a4b-0f60008cfde2", "error": null, "message": null, "elapsed_s": 1.04, "sent": "Cybersecurity awareness is essential for individuals and organizations"}
{"status": 200, "guess": "unsure", "confidence": 0.6152, "model_score": 0.7712, "style_score": 0.9167, "combined_score": 0.8076, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "fdc01b67-6599-4cc1-8c65-d6d8fee532ce", "error": null, "message": null, "elapsed_s": 1.28, "sent": "Reading regularly offers a wide range of benefits for people of all ag"}
{"status": 200, "guess": "unsure", "confidence": 0.6438, "model_score": 0.7903, "style_score": 0.9167, "combined_score": 0.8219, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "a64f64c5-bd59-4d9c-a7dc-1b65892c2f58", "error": null, "message": null, "elapsed_s": 0.92, "sent": "Effective time management is a key skill for achieving both personal a"}
{"status": 200, "guess": "unsure", "confidence": 0.738, "model_score": 0.8531, "style_score": 0.9167, "combined_score": 0.869, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "041c3804-7855-4825-9fa5-e41eabbc4011", "error": null, "message": null, "elapsed_s": 1.55, "sent": "Energy storage technologies are becoming increasingly important as the"}
{"status": 200, "guess": "unsure", "confidence": 0.0358, "model_score": 0.6779, "style_score": 0.4646, "combined_score": 0.5179, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "c963ec62-e72c-464d-95ca-449056600d54", "error": null, "message": null, "elapsed_s": 1.05, "sent": "It is a truth universally acknowledged, that a single man in possessio"}
{"status": 200, "guess": "unsure", "confidence": 0.2974, "model_score": 0.9483, "style_score": 0.5488, "combined_score": 0.6487, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "a96b7d6e-4eb2-4b18-a45c-c426208b8c42", "error": null, "message": null, "elapsed_s": 1.56, "sent": "It was the best of times, it was the worst of times, it was the age of"}
{"status": 200, "guess": "human", "confidence": 0.2752, "model_score": 0.3166, "style_score": 0.5, "combined_score": 0.3624, "label": "We think this was probably written by a person.", "content_id": "59b970b1-312b-4acf-8b36-e699e3aa8a7b", "error": null, "message": null, "elapsed_s": 1.05, "sent": "There is grandeur in this view of life, with its several powers, havin"}
{"status": 200, "guess": "human", "confidence": 0.6378, "model_score": 0.4745, "style_score": 0.0833, "combined_score": 0.1811, "label": "We think this was probably written by a person.", "content_id": "48b73482-e17e-4461-8a9b-4095755c47fe", "error": null, "message": null, "elapsed_s": 1.03, "sent": "You don't know about me, without you have read a book by the name of T"}
{"status": 200, "guess": "human", "confidence": 0.2874, "model_score": 0.4254, "style_score": 0.3333, "combined_score": 0.3563, "label": "We think this was probably written by a person.", "content_id": "67980b7e-17cf-4ce9-8473-bfbc84697259", "error": null, "message": null, "elapsed_s": 1.12, "sent": "Call me Ishmael. Some years ago, never mind how long precisely, having"}
{"status": 200, "guess": "unsure", "confidence": 0.3892, "model_score": 0.6839, "style_score": 0.7268, "combined_score": 0.6946, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "d8b7e348-2648-4204-ad83-eb7ab506cd4c", "error": null, "message": null, "elapsed_s": 1.15, "sent": "Getting enough sleep matters more than most of us admit. It helps the "}
{"status": 200, "guess": "unsure", "confidence": 0.163, "model_score": 0.5708, "style_score": 0.6137, "combined_score": 0.5815, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "df9a902f-f36d-46b5-865a-7f893fc74bac", "error": null, "message": null, "elapsed_s": 1.27, "sent": "Public libraries remain an important resource for communities of all s"}
{"status": 200, "guess": "unsure", "confidence": 0.1126, "model_score": 0.7252, "style_score": 0.5, "combined_score": 0.5563, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "0b7cac26-171d-4bb2-945d-4bdd9f5c96dd", "error": null, "message": null, "elapsed_s": 0.78, "sent": "I think the new bus schedule is mostly fine. It gets me to school on t"}
{"status": 200, "guess": "unsure", "confidence": 0.4328, "model_score": 0.7506, "style_score": 0.705, "combined_score": 0.7164, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "557df58a-cf2a-452c-8fb3-0387847cb770", "error": null, "message": null, "elapsed_s": 1.15, "sent": "The committee reviewed the proposal at its meeting in March. Members n"}
{"status": 200, "guess": "unsure", "confidence": 0.645, "model_score": 0.7911, "style_score": 0.9167, "combined_score": 0.8225, "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.", "content_id": "ec6b2cc7-9b29-4588-b25a-41fed0053554", "error": null, "message": null, "elapsed_s": 0.89, "sent": "In my country we celebrate the new year with a big dinner. All the fam"}
```

Criterion 4, appeal path (the last five rows are the mistyped ids):

```json
{"sent": "Urban green spaces play a vital role in improving the quality of life ", "submit_status": 200, "content_id": "20a2899b-efcb-40d8-af3e-40e822d68878", "appeal_http_status": 200, "appeal_status_field": "under_review", "appeal_entries": 1, "decision_entry_status": "decided", "guess": "under_review"}
{"sent": "Cybersecurity awareness is essential for individuals and organizations", "submit_status": 200, "content_id": "4fc764ba-dd9a-4394-8fa2-afb480d183df", "appeal_http_status": 200, "appeal_status_field": "under_review", "appeal_entries": 1, "decision_entry_status": "decided", "guess": "under_review"}
{"sent": "Reading regularly offers a wide range of benefits for people of all ag", "submit_status": 200, "content_id": "752342c1-f377-4790-bae1-52326f5e8956", "appeal_http_status": 200, "appeal_status_field": "under_review", "appeal_entries": 1, "decision_entry_status": "decided", "guess": "under_review"}
{"sent": "Effective time management is a key skill for achieving both personal a", "submit_status": 200, "content_id": "f974c52f-179a-4e99-8c6b-96309b5f871f", "appeal_http_status": 200, "appeal_status_field": "under_review", "appeal_entries": 1, "decision_entry_status": "decided", "guess": "under_review"}
{"sent": "Energy storage technologies are becoming increasingly important as the", "submit_status": 200, "content_id": "6430a9d8-3429-4d8f-9dea-ea0ddc8f34e6", "appeal_http_status": 200, "appeal_status_field": "under_review", "appeal_entries": 1, "decision_entry_status": "decided", "guess": "under_review"}
{"sent": "It is a truth universally acknowledged, that a single man in possessio", "submit_status": 200, "content_id": "580cfe5b-d182-48b7-a522-4deaa76fd495", "appeal_http_status": 200, "appeal_status_field": "under_review", "appeal_entries": 1, "decision_entry_status": "decided", "guess": "under_review"}
{"sent": "It was the best of times, it was the worst of times, it was the age of", "submit_status": 200, "content_id": "bd80fe5f-d9e0-4f5b-bd41-5a9e22fb9458", "appeal_http_status": 200, "appeal_status_field": "under_review", "appeal_entries": 1, "decision_entry_status": "decided", "guess": "under_review"}
{"sent": "There is grandeur in this view of life, with its several powers, havin", "submit_status": 200, "content_id": "06148c5a-3c85-41dd-84b2-255b540cff4c", "appeal_http_status": 200, "appeal_status_field": "under_review", "appeal_entries": 1, "decision_entry_status": "decided", "guess": "under_review"}
{"sent": "You don't know about me, without you have read a book by the name of T", "submit_status": 200, "content_id": "65f323c1-a988-46ae-bcde-17667939bf6f", "appeal_http_status": 200, "appeal_status_field": "under_review", "appeal_entries": 1, "decision_entry_status": "decided", "guess": "under_review"}
{"sent": "Call me Ishmael. Some years ago, never mind how long precisely, having", "submit_status": 200, "content_id": "994907da-51ff-44af-823c-79b604c6f3ed", "appeal_http_status": 200, "appeal_status_field": "under_review", "appeal_entries": 1, "decision_entry_status": "decided", "guess": "under_review"}
{"sent": "mistyped id 00a2899b-efcb…", "appeal_http_status": 404, "error": "unknown_content_id", "appeal_entries": 0, "guess": "404"}
{"sent": "mistyped id 4fc764b0-dd9a…", "appeal_http_status": 404, "error": "unknown_content_id", "appeal_entries": 0, "guess": "404"}
{"sent": "mistyped id 752342c1-f377…", "appeal_http_status": 404, "error": "unknown_content_id", "appeal_entries": 0, "guess": "404"}
{"sent": "mistyped id f974c52f-179a…", "appeal_http_status": 404, "error": "unknown_content_id", "appeal_entries": 0, "guess": "404"}
{"sent": "mistyped id 6430a9d8-3429…", "appeal_http_status": 404, "error": "unknown_content_id", "appeal_entries": 0, "guess": "404"}
```

Criterion 5, bad input (`log_entries_added` is how many entries the request left in the audit log):

```json
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "content_id": null, "error": "missing_field", "message": "Both 'text' and 'creator_id' are required, and both must be strings.", "elapsed_s": 0.01, "sent": "{\"creator_id\": \"eval_bad_missing\"}", "log_entries_added": 1}
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "content_id": null, "error": "empty_text", "message": "The text is empty.", "elapsed_s": 0.02, "sent": "(empty text)", "log_entries_added": 1}
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "content_id": null, "error": "empty_text", "message": "The text is empty.", "elapsed_s": 0.01, "sent": "   \n\t  ", "log_entries_added": 1}
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "content_id": null, "error": "missing_field", "message": "Both 'text' and 'creator_id' are required, and both must be strings.", "elapsed_s": 0.11, "sent": "{\"text\": null, \"creator_id\": \"eval_bad_null\"}", "log_entries_added": 1}
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "content_id": null, "error": "missing_field", "message": "Both 'text' and 'creator_id' are required, and both must be strings.", "elapsed_s": 0.02, "sent": "{\"text\": 12345, \"creator_id\": \"eval_bad_number\"}", "log_entries_added": 1}
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "content_id": null, "error": "invalid_json", "message": "Send a JSON object with 'text' and 'creator_id'.", "elapsed_s": 0.03, "sent": "[\"text\", \"creator_id\"]", "log_entries_added": 1}
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "content_id": null, "error": "missing_field", "message": "Both 'text' and 'creator_id' are required, and both must be strings.", "elapsed_s": 0.04, "sent": "{\"text\": \"Some perfectly good writing that has no creator attached to it at all, which should be refused cleanly.\"}", "log_entries_added": 1}
{"status": 413, "guess": null, "confidence": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "content_id": null, "error": "text_too_long", "message": "The text is over 20,000 characters.", "elapsed_s": 0.1, "sent": "word word word word word word word word word word word word word word ", "log_entries_added": 1}
```

**Diagnoses**

The numbers behind these, per text (from `results/run_2026-11-07_1716_before_c2-5.md` and `results/attack_run_2026-11-07_1655_before.md`):

| Text | model | style | combined | label |
|---|---|---|---|---|
| AI: green spaces | 0.899 | 0.917 | 0.904 | ai |
| AI: cybersecurity | 0.788 | 0.868 | 0.808 | unsure |
| AI: reading | 0.771 | 0.917 | 0.808 | unsure |
| AI: time management | 0.790 | 0.917 | 0.822 | unsure |
| AI: energy storage | 0.853 | 0.917 | 0.869 | unsure |
| human: Austen | 0.678 | 0.465 | 0.518 | unsure |
| human: Dickens | 0.948 | 0.549 | 0.649 | unsure |
| human: Darwin | 0.317 | 0.500 | 0.362 | human |
| human: Twain | 0.474 | 0.083 | 0.181 | human |
| human: Melville | 0.425 | 0.333 | 0.356 | human |

**Criterion 2, MISSED: Austen (0.518) and Dickens (0.649) scored above the 0.50 ceiling. Stage: signal one. Mechanism:** the model signal measures how predictable text is to gpt2, and both passages are predictable to it: they are very famous, so the model has seen them many times, and Dickens is built from the same phrase repeated ten times ("it was the ... it was the ...") so every repeat is easy to guess. Dickens' model score is 0.948, higher than any AI paragraph's. The style signal read both as mid-range (0.465 and 0.549), so my combining rule had nothing human to lean on. This is the blind spot I wrote down in Milestone 1 (predictable is not machine-written) showing up on the "clearly human" set. It is also a confound in how I chose the set: famous passages are the worst case for signal one, and a real writer's unseen prose would probably score lower. I am not revising the criterion for that. It was measurable and I missed it.

**Criterion 3, MISSED, AI half (1 of 5 reached `ai`, target 3). Stage: the label mapping, with signal one's scale behind it. Mechanism:** both signals agree on all five AI paragraphs (model 0.77 to 0.90, style 0.87 to 0.92), so nothing is wrong with the reading. The combined scores (0.808 to 0.904) simply fall below `AI_THRESHOLD = 0.88` for four of the five, the nearest by 0.011 (energy storage, 0.869). Two things put them there. Signal one's logistic squash (midpoint perplexity 45, steepness 1.6) tops out around 0.9 for ordinary AI text, so the score range is compressed. And my combining rule, when the signals agree, still pulls toward the lower one, so 0.771 and 0.917 give 0.808, where a plain average gives 0.844. I put the threshold at 0.88 in Unit 7 on purpose, to keep plain human writing from being labelled AI, and I wrote then that the cost was AI text landing in *unsure*. This miss is that cost. Lowering it to catch these four (about 0.80) would also label my plain dog paragraph (0.859) and the staff's technical-documentation text FP05 (0.802) as AI. So criteria 1 and 3 pull against each other and I can't meet both at once with this signal pair.

**Criterion 3, MISSED, human half (3 of 5 reached `human`, target 4). Stage: signal one.** The two misses are the same two texts as criterion 2, Austen and Dickens, for the same reason, so this is one problem counted twice, not two.

**The seven broken attacks** (from the Milestone 2 run; "average" is what a plain average of the two signals would have labelled it):

| Attack | Stage | Mechanism |
|---|---|---|
| EV01, typos added to AI text (model 0.164, style 1.000, combined 0.373, human) | **signal one**, amplified by the combining rule | The brief aimed typos at signal two; they actually broke signal one. A misspelled word becomes rare sub-word pieces that gpt2 finds surprising, so perplexity jumps and the model score falls to 0.16. The style signal was *not* fooled (1.000, because my type-token ratio has weight 0). My rule then gives the more-human signal 75%, so the single fooled signal decided it. A plain average gives 0.582, *unsure*, which would have held. |
| EV09, a human opening paragraph bolted onto AI text (model 0.704, style 0.331, combined 0.424, human) | **signal two**, with the combining rule and the label mapping | The casual opening has uneven sentences, which raises the sentence-length spread and drops the style score to 0.331. Signal one still read it as AI-leaning (0.704), but the rule leaned toward the human signal and the result landed 0.026 under `HUMAN_THRESHOLD = 0.45`. A plain average gives 0.518, *unsure*. |
| EV02, "Really." after every sentence (model 0.594, style 0.000, combined 0.149) | **signal two** | One-word sentences make the length spread huge, and spread is the only measure the style signal counts, so style went to 0. A plain average is still 0.297, human. |
| EV06, one very long and one very short sentence (model 0.573, style 0.083, combined 0.206) | **signal two** | Same mechanism: two extreme sentences inflate the spread. Average 0.328, still human. |
| EV05, heavy human editing pass (model 0.321, style 0.000, combined 0.080) | **neither signal is wrong; the limit of the method** | Both signals read the text as human because it largely is: after a heavy rewrite the surface statistics are a person's. No measure of text shape or predictability can see where the draft came from. |
| PI01 and PI02, injected "instructions" (combined 0.178 and 0.114, human) | **signal two, and signal one on short text** | Nothing here reads instructions, so they were not obeyed. The injected lines are short imperative sentences ("Ignore all previous instructions."), which raise the length spread (style 0.083 for both), and the unusual instruction wording raises perplexity (model 0.463 and 0.204, against 0.754 for the same fragment without it). The fragments are also only 42 to 45 words, and the same fragment without the instruction already scores 0.439 (human). |

**The pattern.** These are not ten separate problems. Both signals respond to how *even and predictable the surface of a text is*, not to who wrote it, and that produces three failures:

1. **Plain human text and generic AI text overlap.** AI paragraphs combine at 0.81 to 0.90 and plain or formal human text at 0.57 to 0.86, so no AI threshold separates them. That is criterion 3's AI half, the four "unsure" real writers in the attack run (FP02 to FP05), and the reason criterion 1 is at risk.
2. **One cheaply fooled signal decides the result.** Typos move signal one, and chopped or one-word sentences move signal two. Four of the seven broken attacks (EV02, EV06, PI01, PI02) are the style signal's spread being inflated, and EV01 is signal one being deflated. This is where a design choice of mine matters: I made the combining rule favour the more-human signal at 75% to protect real writers, and it turned EV01 and EV09 from held into broke. In the false-positive set the same rule changed only the labels of FP01 and FP06 against a plain average (human against unsure), and no real writer was accused either way.
3. **Predictable human text reads as AI.** Famous or repetitive prose (Austen, Dickens) scores high on signal one. That is criterion 2's ceiling miss and criterion 3's human half.

So the two decisions I took in Milestone 1 and Unit 7 to keep real writers safe, a high AI threshold and a rule that leans human, are directly the cause of criterion 3's AI miss and two evasion breaks. That is the trade I said I was making, and these are its measured costs.

**Criteria I did not revise.** Every miss was measurable and I missed it, so none of my criteria are revised. Two of the five criteria missed, so the targets were not trivially easy.

**Things you should know about this run.** I ran criteria 2 to 5 once as a one-trial smoke test of my `run_eval.py` additions before the real run, and deleted that file; the service is deterministic and the real run matched it. During the first attempt at the real run I found four stale `app.py` servers left over from earlier milestones (my cleanup had killed the launcher but not its child), killed them all and reran against one server from a clean start, so the recorded run is against a single current process. The audit log keeps the entries from the aborted attempt.

---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
