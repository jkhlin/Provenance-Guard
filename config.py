"""
Settings for Provenance Guard.

Everything you're likely to change lives here, at the top, on purpose.

You'll edit the thresholds in Milestone 5 and the rate limits in unit 8.
"""

import os
from pathlib import Path

ROOT = Path(__file__).parent


# ─── The service ─────────────────────────────────────────────────────────────

# `127.0.0.1` is loopback — only your own machine can reach it, which is what
# you want all through units 7 and 8. A host somewhere else has to accept
# traffic from outside the box, and that means `0.0.0.0`. Setting the env var
# is how you get it; the default keeps your local `curl` commands unchanged.
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))

# Flask's debug mode gives anyone who can reach the service an interactive
# Python prompt inside your process. Fine on loopback, a gift to strangers
# anywhere else — so it turns itself off the moment HOST isn't loopback.
DEBUG = os.getenv("AI201_DEBUG", "1") == "1" and HOST in ("127.0.0.1", "localhost")


# ─── The local model ─────────────────────────────────────────────────────────
# Your first signal runs a language model ON YOUR OWN MACHINE. No account, no
# key, no card. It downloads about 550 MB the first time — do that before
# class, not during it.
#
# What it measures: how *predictable* your text is to a language model. Text a
# model finds easy to predict tends to be text a model wrote.
#
# The first call is the slow one — ten to twenty seconds while the model loads,
# longer on an older laptop. After that it stays in memory and a submission
# takes a second or two. That cost is part of what you're learning: this is
# what running a model inline in a request actually looks like.

DETECTOR_MODEL = os.getenv("AI201_DETECTOR_MODEL", "gpt2")

# Longer text gives a steadier reading but takes longer. 400 tokens is roughly
# 300 words, which is enough for the signal to mean something.
DETECTOR_MAX_TOKENS = 400


# What /submit will accept. Below the minimum the signals aren't meaningful;
# above the maximum the request is refused before it reaches the model, and
# only the first DETECTOR_MAX_TOKENS tokens are scored either way.
MIN_TEXT_WORDS = 20
MAX_TEXT_CHARS = 20_000
MAX_CREATOR_ID_CHARS = 100
MAX_REASONING_CHARS = 2_000   # an appeal's reasoning


# ─── Scoring (Milestone 4) ───────────────────────────────────────────────────
# The combining rule (scoring.py::combine_signals): when the two signals split,
# the one that reads MORE HUMAN counts for this much, and the more-AI one for
# the rest. 0.5 is a plain average; higher leans toward the human reading.
#
# Unit 7 set this to 0.75, to keep real writers off the AI label. Unit 8's
# attack run showed the cost: one cheaply fooled signal then decides the whole
# score (typos on signal one, chopped sentences on signal two). Changed to 0.5
# in unit 8, Milestone 5. The before/after is in the README, "The Improvement".

WEIGHT_MORE_HUMAN_SIGNAL = 0.5


# ─── Thresholds (Milestone 5) ────────────────────────────────────────────────
# Where one label becomes another. Scores run 0.0 (confidently human) to 1.0
# (confidently AI).
#
#   score < HUMAN_THRESHOLD          -> high-confidence human
#   between the two                  -> unsure
#   score > AI_THRESHOLD             -> high-confidence AI
#
# ⚠️ This is where your false-positive decision from Milestone 1 actually gets
# made. Widening the unsure band means fewer wrong accusations and more AI text
# getting through. There is no setting that avoids the trade — only settings
# that decide who pays for it.

# Chosen from fourteen texts I scored (see README, "Label Variants"). Generic
# AI text combined at about 0.90. The plainest human texts combined at up to
# 0.86. 0.88 sits in that gap, which is only about 0.02 wide each side, so
# treat it as fragile: a plainer human text than any I tried will cross it.
# It is high on purpose. The AI label should only fire on text both signals
# agree about, because accusing a real writer costs far more than missing AI.
AI_THRESHOLD = 0.88

# Human is the cheap error to make, so this is set generously: formal human
# prose (0.42) and a quirky human paragraph (0.45) both need to reach it.
HUMAN_THRESHOLD = 0.45

# Every label has to be reachable, and `scoring.label_ranges()` prints the
# bands. Reaching "ai" needs BOTH signals high, because combine_signals leans
# toward the more-human one.


# ─── Rate limiting (UNIT 8) ──────────────────────────────────────────────────
# On for unit 8 (set AI201_RATE_LIMITS=0 to switch it off). Numbers chosen in Milestone 1.
#
# Think about two people: a real writer submitting their own work a few times
# an hour, and a script sending a thousand variations to map your thresholds.
# Your README has to say why your numbers and not others.

RATE_LIMITING_ENABLED = os.getenv("AI201_RATE_LIMITS", "1") == "1"

RATE_LIMIT_PER_MINUTE = 5
RATE_LIMIT_PER_DAY = 50

# Flask-Limiter warns loudly without this. In-memory is right for one laptop
# and wrong for anything real — a restart forgets every count, and two copies
# of the service wouldn't share limits.
RATE_LIMIT_STORAGE = "memory://"


# ─── Paths ───────────────────────────────────────────────────────────────────

LOG_DIR = ROOT / "logs"
AUDIT_LOG = LOG_DIR / "audit.jsonl"
RESULTS_DIR = ROOT / "results"
