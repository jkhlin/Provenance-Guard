# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. My own plain writing is almost never called AI

Of 10 pieces I wrote myself, **at most 1 is labelled high-confidence AI**, and
that has to hold in **all three trials**. At least 4 of the 10 must be
deliberately plain: short sentences, everyday words, no unusual punctuation. That
is the writing signals one and two are most likely to get wrong.

**Why this target:** On a writing site a wrong accusation costs the writer far
more than a missed detection costs the site, so this is the tightest number I
set. I picked 1 in 10 rather than 0 because the plain pieces are meant to be
hard and I'd rather aim at something I might miss than something I can't. Loading
4 of the 10 with plain prose stops me passing by testing only the easy case.

---

## 2. Clearly-AI and clearly-human text score far apart

On 5 texts I'm confident are AI-generated and 5 I'm confident a person wrote,
the **mean `combined_score` of the AI set is at least 0.30 higher** than the mean
of the human set, and **no clearly-human text scores above 0.50**. I pick and
sort all ten before running anything, and the gap has to hold in each of the
three trials.

**Why this target:** If the two groups barely separate, the labels are noise
however I set the thresholds. 0.30 is about the width of my unsure band
(0.35 to 0.65 as placeholders), so the clear cases land on opposite sides of it
and not both inside it. The "no human above 0.50" half guards the same worry as
criterion 1 from the other direction: an average can look fine while one real
writer sits near the AI side.

---

## 3. All three labels are reachable and mostly right

Over 15 inputs I sort by hand beforehand (5 clearly AI, 5 clearly human, 5
borderline), in every trial:

- at least **3 of the 5 clearly-AI** texts get the `ai` label,
- at least **4 of the 5 clearly-human** texts get the `human` label,
- at least **4 of the 5 borderline** texts get the `unsure` label.

**Why this target:** A label nothing can produce is a hole in the service, and
the config notes warn that a weak style signal can make `human` unreachable. The
three thresholds are deliberately uneven. The `ai` label is meant to be hard to
reach (criterion 1 pushes it up), so I only ask 3 of 5 of it. Pulling the
other way, `human` should be easy to earn, and the borderline cases are exactly
what the unsure band exists for, so those get 4 of 5.

---

## 4. An appeal always changes status and always leaves a record

For 10 submissions I then appeal using the `content_id` from each response:
**10 of 10 return `200` with `status: "under_review"`**, and each adds exactly one
appeal entry to `/log` under that `content_id`, with the original decision entry
still there unchanged. Separately, **5 of 5 appeals using a wrong or mistyped
`content_id` return `404`** and add no appeal entry. All of this holds in each of
the three trials.

**Why this target:** The appeal is the only thing between a wrong accusation and
nothing, so it gets the one 100% target. A route that sometimes drops an appeal
is worse than one that doesn't exist, because the writer thinks they were heard.
A silent success on a typo'd id is the most common way this fails, so I test the
404 explicitly.

---

## 5. Bad input is refused cleanly, never a crash

I send 8 malformed requests: missing `text`, empty `text`, whitespace-only `text`,
`text: null`, `text` as a number, a body that is a JSON list instead of an object,
a missing `creator_id`, and a 50,000-word `text`. **None returns a `500`**. Every
one returns a `400` or `413` with the `error` and `message` fields from my
contract. Every one adds a `rejected` entry to the log. The enormous one answers
in **under 5 seconds**. All of this holds in each of the three trials.

**Why this target:** A crash on malformed input is one of the most common real
failures, and one that never reaches the audit log is invisible. Checking the
log entry as well as the status code catches the case where I return a tidy 400
but leave no trace. The 5-second limit is there because a 50,000-word body must
be refused before it reaches the model. If it gets scored, the request hangs for
a long time instead of failing fast.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
