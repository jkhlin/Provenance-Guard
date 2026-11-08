"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.
"""

# ── Inputs, sorted by hand BEFORE any run (criteria 2 and 3) ────────────────
# "Clearly AI": five paragraphs written by an AI model, in the usual register.
AI_TEXTS = [
    "Urban green spaces play a vital role in improving the quality of life for city residents. They provide opportunities for physical activity, relaxation, and social interaction. In addition, parks and gardens help to reduce air pollution and lower temperatures during hot summer months. They also support local biodiversity by offering habitats for birds, insects, and other wildlife. City planners should therefore prioritize the creation and maintenance of these spaces. By doing so, communities can become healthier, more resilient, and more enjoyable places to live.",
    "Cybersecurity awareness is essential for individuals and organizations in today's digital world. Many data breaches occur because of simple human errors, such as using weak passwords or clicking on suspicious links. Regular training can help employees recognize common threats and respond appropriately. Furthermore, implementing multi-factor authentication adds an important layer of protection. Organizations should also ensure that their software is updated regularly to address known vulnerabilities. Ultimately, a strong security culture is the most effective defense against evolving cyber threats.",
    "Reading regularly offers a wide range of benefits for people of all ages. It improves vocabulary, strengthens concentration, and enhances critical thinking skills. Additionally, reading fiction can foster empathy by allowing individuals to experience different perspectives. Studies have also shown that reading before bed can reduce stress and improve sleep quality. Parents and teachers can encourage this habit by providing access to a variety of engaging books. In conclusion, cultivating a love of reading is a valuable investment in lifelong learning and well-being.",
    "Effective time management is a key skill for achieving both personal and professional goals. It begins with setting clear priorities and identifying the tasks that matter most. Breaking large projects into smaller, manageable steps can make progress feel more achievable. It is also important to minimize distractions, such as unnecessary notifications and multitasking. Regular breaks help maintain focus and prevent burnout over the long term. By adopting these strategies, individuals can increase their productivity while maintaining a healthy work-life balance.",
    "Energy storage technologies are becoming increasingly important as the world transitions to renewable power. Solar and wind generation fluctuate depending on the weather, which can create challenges for the electrical grid. Batteries can store excess energy during periods of high production and release it when demand is high. This helps to stabilize supply and reduce reliance on fossil fuel power plants. Continued research is also improving the cost and lifespan of these systems. As a result, energy storage will play a central role in building a sustainable energy future.",
]

# "Clearly human": five well-known public-domain passages, so a person
# certainly wrote them (Austen, Dickens, Darwin, Twain, Melville). Caveat: a
# language model has seen these many times, which can make them read as
# predictable to signal one. That is a known confound, not a bug in the test.
HUMAN_TEXTS = [
    "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife. However little known the feelings or views of such a man may be on his first entering a neighbourhood, this truth is so well fixed in the minds of the surrounding families, that he is considered the rightful property of some one or other of their daughters.",
    "It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity, it was the season of Light, it was the season of Darkness, it was the spring of hope, it was the winter of despair. There were a king with a large jaw and a queen with a plain face, on the throne of England; there were a king with a large jaw and a queen with a fair face, on the throne of France.",
    "There is grandeur in this view of life, with its several powers, having been originally breathed into a few forms or into one; and that, whilst this planet has gone cycling on according to the fixed law of gravity, from so simple a beginning endless forms most beautiful and most wonderful have been, and are being, evolved.",
    "You don't know about me, without you have read a book by the name of The Adventures of Tom Sawyer; but that ain't no matter. That book was made by Mr. Mark Twain, and he told the truth, mainly. There was things which he stretched, but mainly he told the truth. That is nothing. I never seen anybody but lied one time or another, without it was Aunt Polly, or the widow, or maybe Mary.",
    "Call me Ishmael. Some years ago, never mind how long precisely, having little or no money in my purse, and nothing particular to interest me on shore, I thought I would sail about a little and see the watery part of the world. It is a way I have of driving off the spleen and regulating the circulation.",
]

# "Borderline": texts I could not call before running. Two are an AI draft with
# human edits or a human aside; three are plain or formal writing of mixed or
# unclear origin (I wrote the last three myself for the test).
BORDERLINE_TEXTS = [
    "Getting enough sleep matters more than most of us admit. It helps the brain sort out what happened during the day, and it keeps mood steady too. Adults generally need seven to nine hours, though plenty of people get far less. A consistent bedtime helps, and so does keeping screens out of the bedroom. Caffeine late in the day is a common culprit, and I'd say it's the one people ignore most. Small changes add up faster than you'd think.",
    "Public libraries remain an important resource for communities of all sizes. They provide free access to books, computers, and educational programs. Honestly, I only really started using ours last year, when the heating at home broke and I needed somewhere warm to work. The staff were friendlier than I expected and nobody minded how long I stayed. Libraries also serve as safe gathering places for people of every age and background.",
    "I think the new bus schedule is mostly fine. It gets me to school on time, but the evening buses are too far apart. Some people at my school say it is worse than before, and I can see why they would feel that way.",
    "The committee reviewed the proposal at its meeting in March. Members noted that the budget had been prepared on the basis of last year's figures. Two members raised concerns about the timetable, which they considered optimistic. It was agreed that the proposal would return to the committee in June with a revised schedule. The chair thanked the working group for its efforts.",
    "In my country we celebrate the new year with a big dinner. All the family comes to the house of my grandmother. We eat many kinds of food and we give small gifts to the children. After dinner we go outside to watch the fireworks. I miss this tradition very much when I am far from home. This year I will make the dinner for my friends here.",
]

SCENARIOS = [
    {
        # Criterion 1: of 10 pieces I wrote myself, at most 1 labelled "ai", at
        # least 4 of them deliberately plain.
        "name": "my own writing",
        "criterion": 1,
        "texts": [
            "REPLACE ME with ten pieces of your own writing, at least four of them plain and simple.",
        ],
    },
    {
        # Criterion 2: mean combined_score of the AI set at least 0.30 above the
        # human set's, and no clearly-human text above 0.50.
        "name": "score spread",
        "criterion": 2,
        "texts": AI_TEXTS + HUMAN_TEXTS,
    },
    {
        # Criterion 3: >=3 of 5 AI get "ai", >=4 of 5 human get "human",
        # >=4 of 5 borderline get "unsure". Order is AI, human, borderline.
        "name": "label coverage",
        "criterion": 3,
        "texts": AI_TEXTS + HUMAN_TEXTS + BORDERLINE_TEXTS,
    },
    {
        # Criterion 4: 10 of 10 appeals return 200 / under_review and add exactly
        # one appeal entry; 5 of 5 mistyped ids return 404 and add none. This
        # needs a submit THEN an appeal, so it uses the "appeal" kind I added to
        # run_eval.py.
        "name": "appeal path",
        "criterion": 4,
        "kind": "appeal",
        "texts": AI_TEXTS + HUMAN_TEXTS,
        "bad_ids": 5,
    },
    {
        # Criterion 5: eight malformed requests, none a 500, every one a 400 or
        # 413 with error + message, every one logged, the 50,000-word one in
        # under 5 s. Two have no usable creator_id, so they count against the
        # caller's ADDRESS; the cooldown keeps the three trials from tripping
        # the per-minute limit on each other.
        "name": "bad input",
        "criterion": 5,
        "check_log": True,
        "cooldown_s": 62,
        "bodies": [
            {"creator_id": "eval_bad_missing"},
            {"text": "", "creator_id": "eval_bad_empty"},
            {"text": "   \n\t  ", "creator_id": "eval_bad_whitespace"},
            {"text": None, "creator_id": "eval_bad_null"},
            {"text": 12345, "creator_id": "eval_bad_number"},
            ["text", "creator_id"],
            {"text": "Some perfectly good writing that has no creator attached to it at all, which should be refused cleanly."},
            {"text": "word " * 50000, "creator_id": "eval_bad_huge"},
        ],
    },
]

def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, (dict, list)):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict or list — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
