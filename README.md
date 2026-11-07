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

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->



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
| high-confidence human |  |  |
| unsure |  |  |
| high-confidence AI |  |  |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "The implementation of the proposed framework requires careful consideration of several key factors. First, it is important to note that the system must be able to handle a wide variety of different inputs. Additionally, the overall performance of the solution depends on a number of important variables.", "creator_id": "jason"}'
```

> Milestone 3 state: signal one only. `style_score` is `null` and `guess`,
> `confidence` and `label` are placeholders until the second signal, the
> combining rule and the labels exist.

```json
{
  "confidence": 0.0,
  "content_id": "4931813a-b6b0-4bf3-8514-f9db3e5ce60d",
  "guess": "pending",
  "label": "placeholder",
  "model_score": 0.8864,
  "style_score": null
}
```

A bad request, to show the refusal shape (HTTP 400):

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "hi there", "creator_id": "jason"}'
```

```json
{
  "error": "text_too_short",
  "message": "Send at least 20 words."
}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "...", "reasoning": "..."}'
```

```json

```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=5"
```

```json
{
  "count": 5,
  "entries": [
    {
      "combined_score": null,
      "content_id": "4931813a-b6b0-4bf3-8514-f9db3e5ce60d",
      "creator_id": "jason",
      "guess": "pending",
      "label": "placeholder",
      "model_score": 0.8864,
      "status": "decided",
      "style_score": null,
      "timestamp": "2026-11-07T22:48:02+00:00"
    },
    {
      "combined_score": null,
      "content_id": "1460dbef-4e71-4060-a499-5c4528ccdfd3",
      "creator_id": "jason",
      "guess": "pending",
      "label": "placeholder",
      "model_score": 0.3666,
      "status": "decided",
      "style_score": null,
      "timestamp": "2026-11-07T22:48:02+00:00"
    },
    {
      "creator_id": "jason",
      "event": "rejected",
      "reason": "missing_field",
      "status": "rejected",
      "timestamp": "2026-11-07T22:48:02+00:00"
    },
    {
      "creator_id": "jason",
      "event": "rejected",
      "reason": "text_too_short",
      "status": "rejected",
      "timestamp": "2026-11-07T22:48:02+00:00"
    },
    {
      "creator_id": "unknown",
      "event": "rejected",
      "reason": "invalid_json",
      "status": "rejected",
      "timestamp": "2026-11-07T22:48:02+00:00"
    }
  ]
}
```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

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
