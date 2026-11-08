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

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



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
