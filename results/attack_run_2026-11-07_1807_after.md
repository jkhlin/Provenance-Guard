# Attack run — after

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-07 18:07
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `17e8e7bf-7657-454e-89c1-7dbf645d610b` | unsure | 0.163 | HELD |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `a925d2e7-2ab5-4e34-b619-71a8f8b93523` | human | 0.406 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `8eef26bd-063b-4dcc-bbcf-2356dc3a7103` | unsure | 0.058 | HELD |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `4972ad9e-39bb-4848-99b5-c2197c7b1c59` | unsure | 0.611 | HELD |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `64002be5-8372-4546-9e60-3ec86e96aeb3` | human | 0.679 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `fff4a359-5522-416b-91af-f491d4c334a4` | human | 0.344 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | `8eb444fe-754d-438e-ad68-e557c25cd315` | unsure | 0.086 | HELD |
| EV08 | evasion | signal one: text below the token window | 400 | `—` | — | — | HELD |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `5284d598-ef1d-4caa-9daa-fa991bae4110` | unsure | 0.035 | HELD |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `f2d6a89b-36dd-4f07-9088-8f3d35cf91a6` | unsure | 0.487 | HELD |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `92b44722-5063-4bbd-a817-ed843f63eb42` | unsure | 0.026 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | `c2666891-c657-4836-a7a6-feba8e56bf15` | unsure | 0.638 | HELD |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `47501eec-e34c-4eee-bcb3-97ef6bfa99a9` | unsure | 0.485 | HELD |
| FP04 | false_positive | a student essay written to a rubric | 200 | `1fab80dc-29a4-400a-9e37-8957ad2ad1c2` | unsure | 0.416 | HELD |
| FP05 | false_positive | technical documentation written by a person | 200 | `b5cbb51d-8710-413d-8664-778a34a13e49` | unsure | 0.608 | HELD |
| FP06 | false_positive | a person imitating a formal template | 200 | `65c9dac3-7e9a-4cfb-a6f3-00587f3cd530` | unsure | 0.133 | HELD |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `01dbd9bb-c649-4acb-8040-e1ee46701f83` | human | 0.118 | HELD |
| FP08 | false_positive | very short genuine human submission | 400 | `—` | — | — | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `6c62e49d-62bd-4b85-ba39-c3c54258cc4c` | human | 0.454 | BROKE |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `3d92477d-d83d-4400-8e2e-d056504a501d` | human | 0.712 | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `1f9e1a1f-7693-4f6e-b81e-cfaa6c999c47` | unsure | 0.166 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `4b0fea48-31fb-4b93-ab80-6f031822b6dd` | unsure | 0.004 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `39b2b8cf-a490-49f7-9747-926e986cf9be` | unsure | 0.110 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | `87e6bd2c-f38b-4ca6-8ef4-950c1fd1eba2` | unsure | 0.055 | HELD |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — | HELD |
| MF02 | malformed | text is a single character | 400 | `—` | — | — | HELD |
| MF03 | malformed | text is control characters | 400 | `—` | — | — | HELD |
| MF04 | malformed | text is only punctuation | 400 | `—` | — | — | HELD |
| MF05 | malformed | text is a very long single word | 400 | `—` | — | — | HELD |
| MF06 | malformed | text is emoji only | 400 | `—` | — | — | HELD |
| MF07 | malformed | text is right-to-left script | 400 | `—` | — | — | HELD |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — | HELD |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — | HELD |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — | HELD |
| RQ03 | malformed | text is a number | 400 | `—` | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | `—` | — | — | HELD |
| RQ05 | malformed | text is null | 400 | `—` | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — | HELD |
| RQ09 | malformed | body is empty | 400 | `—` | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | `—` | — | — | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | `—` | — | — | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "17e8e7bf-7657-454e-89c1-7dbf645d610b",
  "creator_id": "attacker_EV01",
  "guess": "unsure",
  "confidence": 0.1634,
  "model_score": 0.1635,
  "style_score": 1.0,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "a925d2e7-2ab5-4e34-b619-71a8f8b93523",
  "creator_id": "attacker_EV02",
  "guess": "human",
  "confidence": 0.4056,
  "model_score": 0.5943,
  "style_score": 0.0,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "8eef26bd-063b-4dcc-bbcf-2356dc3a7103",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.0578,
  "model_score": 0.6662,
  "style_score": 0.3916,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "4972ad9e-39bb-4848-99b5-c2197c7b1c59",
  "creator_id": "attacker_EV04",
  "guess": "unsure",
  "confidence": 0.6114,
  "model_score": 0.6114,
  "style_score": 1.0,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "64002be5-8372-4546-9e60-3ec86e96aeb3",
  "creator_id": "attacker_EV05",
  "guess": "human",
  "confidence": 0.6788,
  "model_score": 0.3212,
  "style_score": 0.0,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "fff4a359-5522-416b-91af-f491d4c334a4",
  "creator_id": "attacker_EV06",
  "guess": "human",
  "confidence": 0.344,
  "model_score": 0.5727,
  "style_score": 0.0833,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "8eb444fe-754d-438e-ad68-e557c25cd315",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.0862,
  "model_score": 0.5862,
  "style_score": 0.5,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_EV08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "5284d598-ef1d-4caa-9daa-fa991bae4110",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.0354,
  "model_score": 0.7042,
  "style_score": 0.3312,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "f2d6a89b-36dd-4f07-9088-8f3d35cf91a6",
  "creator_id": "attacker_EV10",
  "guess": "unsure",
  "confidence": 0.4868,
  "model_score": 0.9792,
  "style_score": 0.5076,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "92b44722-5063-4bbd-a817-ed843f63eb42",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.0262,
  "model_score": 0.6175,
  "style_score": 0.3562,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "c2666891-c657-4836-a7a6-feba8e56bf15",
  "creator_id": "attacker_FP02",
  "guess": "unsure",
  "confidence": 0.6378,
  "model_score": 0.7387,
  "style_score": 0.8991,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "47501eec-e34c-4eee-bcb3-97ef6bfa99a9",
  "creator_id": "attacker_FP03",
  "guess": "unsure",
  "confidence": 0.4846,
  "model_score": 0.8051,
  "style_score": 0.6795,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "1fab80dc-29a4-400a-9e37-8957ad2ad1c2",
  "creator_id": "attacker_FP04",
  "guess": "unsure",
  "confidence": 0.4162,
  "model_score": 0.8329,
  "style_score": 0.5833,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "b5cbb51d-8710-413d-8664-778a34a13e49",
  "creator_id": "attacker_FP05",
  "guess": "unsure",
  "confidence": 0.6082,
  "model_score": 0.8005,
  "style_score": 0.8078,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "65c9dac3-7e9a-4cfb-a6f3-00587f3cd530",
  "creator_id": "attacker_FP06",
  "guess": "unsure",
  "confidence": 0.133,
  "model_score": 0.8814,
  "style_score": 0.2517,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "01dbd9bb-c649-4acb-8040-e1ee46701f83",
  "creator_id": "attacker_FP07",
  "guess": "human",
  "confidence": 0.1184,
  "model_score": 0.8816,
  "style_score": 0.0,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_FP08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "6c62e49d-62bd-4b85-ba39-c3c54258cc4c",
  "creator_id": "attacker_PI01",
  "guess": "human",
  "confidence": 0.4542,
  "model_score": 0.4625,
  "style_score": 0.0833,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "3d92477d-d83d-4400-8e2e-d056504a501d",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.7122,
  "model_score": 0.2044,
  "style_score": 0.0833,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "1f9e1a1f-7693-4f6e-b81e-cfaa6c999c47",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.1656,
  "model_score": 0.5943,
  "style_score": 0.5712,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "4b0fea48-31fb-4b93-ab80-6f031822b6dd",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.004,
  "model_score": 0.4998,
  "style_score": 0.5041,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "39b2b8cf-a490-49f7-9747-926e986cf9be",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.1104,
  "model_score": 0.6401,
  "style_score": 0.4702,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "87e6bd2c-f38b-4ca6-8ef4-950c1fd1eba2",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.0552,
  "model_score": 0.5583,
  "style_score": 0.3864,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't reliable enough to say, so please don't read this as a judgment about your work. If it doesn't look right to you, you can appeal using your submission ID.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF06",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF07",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
