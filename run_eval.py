#!/usr/bin/env python3
"""
Run your five criteria three times each.  <- UNIT 8, MILESTONE 3

    python app.py                              # in one terminal
    python run_eval.py --label before          # in another
    python run_eval.py --label after

The attack set tests what staff thought to test. This tests what *you* thought
to test, and the two rarely overlap much. Both count.

Fill in `scenarios.py` first — that's where you say what each criterion needs
run against it. A criterion about false positives needs your own writing. One
about label coverage needs inputs across the score range.

!! Three trials, and **your first signal runs a model, so identical input can
score differently twice.** That's exactly why repeats matter here.

This does the sending and the recording. It does not decide whether a trial
passed — that depends on the criterion you wrote, so the Verdict column comes
back blank.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import config

# Windows consoles often run a codepage that can't print every character in
# this file's help text. Without this, `--help` ends in a UnicodeEncodeError
# traceback instead of the help — which is a miserable first thing to hit.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):  # not a normal text stream
        pass


DEFAULT_URL = f"http://{config.HOST}:{config.PORT}"


def bodies_for(scenario):
    """
    The request bodies one scenario sends.

    A "texts" scenario gets a creator_id made up for it. A "bodies" scenario is
    sent exactly as written, which is how a bad-input criterion says things a
    string can't — no `text` field, a null, something enormous.
    """
    if scenario.get("bodies"):
        return list(scenario["bodies"])
    return [
        {"text": text, "creator_id": f"eval_{scenario['name'][:12]}_{i}"}
        for i, text in enumerate(scenario["texts"], 1)
    ]


def describe(body):
    """A short, readable note of what was sent — for the report."""
    if isinstance(body, dict) and set(body) == {"text", "creator_id"} and isinstance(body.get("text"), str):
        text = body["text"]
        return text[:70] if text else "(empty text)"
    return json.dumps(body)[:120]


# ── Extensions I added for my own criteria (unit 8, Milestone 3) ──────────────
# The starter only sends /submit and records five fields. My criteria also need
# the appeal path, the combined score, error bodies, timing, and whether a
# request left a log entry. Everything below is additive; a scenario that uses
# none of it runs exactly as before.

def log_size(requests, url):
    return requests.get(f"{url}/health", timeout=10).json().get("log_entries")


def submit_once(requests, args, body, check_log=False):
    """POST one body to /submit and record what came back."""
    import time

    preview = describe(body)
    before = log_size(requests, args.url) if check_log else None
    started = time.perf_counter()
    try:
        response = requests.post(f"{args.url}/submit", json=body, timeout=args.timeout)
        elapsed = round(time.perf_counter() - started, 2)
        try:
            payload = response.json() if response.content else {}
        except ValueError:
            payload = {"_not_json": response.text[:80]}
        result = {
            "status": response.status_code,
            "guess": payload.get("guess"),
            "confidence": payload.get("confidence"),
            "model_score": payload.get("model_score"),
            "style_score": payload.get("style_score"),
            "combined_score": payload.get("combined_score"),
            "label": payload.get("label"),
            "content_id": payload.get("content_id"),
            "error": payload.get("error"),
            "message": payload.get("message"),
            "elapsed_s": elapsed,
            "sent": preview,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": None, "error": f"{type(exc).__name__}: {exc}", "sent": preview}
    if check_log:
        result["log_entries_added"] = log_size(requests, args.url) - before
    return result


def appeal_trial(requests, args, scenario):
    """
    Submit each text, appeal it with the content_id that came back, and check
    the log. Then appeal with `bad_ids` mistyped ids and check each is refused
    and leaves no appeal entry.
    """
    results, ids = [], []
    for i, body in enumerate(bodies_for(scenario), 1):
        sub = submit_once(requests, args, body)
        cid = sub.get("content_id")
        ids.append(cid)
        row = {"sent": sub["sent"], "submit_status": sub["status"], "content_id": cid}
        if cid:
            reply = requests.post(f"{args.url}/appeal", timeout=args.timeout,
                                  json={"content_id": cid, "reasoning": "Eval check: I wrote this myself."})
            row["appeal_http_status"] = reply.status_code
            row["appeal_status_field"] = reply.json().get("status")
        results.append(row)

    log = requests.get(f"{args.url}/log", timeout=30).json()["entries"]
    for row in results:
        cid = row.get("content_id")
        mine = [e for e in log if e.get("content_id") == cid]
        row["appeal_entries"] = sum(1 for e in mine if e.get("event") == "appeal")
        row["decision_entry_status"] = next((e.get("status") for e in mine if e.get("event") is None), None)
        row["guess"] = row.get("appeal_status_field") or "no-appeal"

    good = [c for c in ids if c]
    for k in range(scenario.get("bad_ids", 0)):
        if not good:
            break
        cid = good[k % len(good)]
        pos = (k * 7) % len(cid)
        bad = cid[:pos] + ("0" if cid[pos] != "0" else "1") + cid[pos + 1:]
        reply = requests.post(f"{args.url}/appeal", timeout=args.timeout,
                              json={"content_id": bad, "reasoning": "Eval check: wrong id."})
        after = requests.get(f"{args.url}/log", timeout=30).json()["entries"]
        results.append({
            "sent": f"mistyped id {bad[:13]}…",
            "appeal_http_status": reply.status_code,
            "error": reply.json().get("error"),
            "appeal_entries": sum(1 for e in after
                                  if e.get("content_id") == bad and e.get("event") == "appeal"),
            "guess": str(reply.status_code),
        })
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--label", default="")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    try:
        import requests
    except ImportError:
        print("The `requests` package isn't installed.\n"
              "Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    try:
        import scenarios
    except ImportError:
        print("No scenarios.py found. Milestone 3 starts by filling it in.",
              file=sys.stderr)
        sys.exit(1)

    problems = scenarios.validate()
    if problems:
        print("scenarios.py has problems:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    try:
        requests.get(f"{args.url}/health", timeout=5)
    except Exception:  # noqa: BLE001
        print(f"Nothing answering at {args.url}. Start it:  python app.py",
              file=sys.stderr)
        sys.exit(1)

    if args.trials < 3:
        print(f"!! {args.trials} trial(s). The submission asks for three.\n")

    rows = []
    for scenario in scenarios.SCENARIOS:
        print(f"\n{scenario['name']}  (criterion {scenario.get('criterion') or '—'})")

        trials = []
        for trial in range(1, args.trials + 1):
            if scenario.get("kind") == "appeal":
                results = appeal_trial(requests, args, scenario)
            else:
                results = [submit_once(requests, args, body,
                                       check_log=scenario.get("check_log", False))
                           for body in bodies_for(scenario)]

            trials.append(results)
            guesses = [r.get("guess") or str(r.get("status") or "—") for r in results]
            print(f"  trial {trial}: {', '.join(guesses)}")

            # The limiter keys on the caller's address when a request has no
            # usable creator_id, so back-to-back trials of such a scenario
            # would trip it. Wait out the window between trials.
            if scenario.get("cooldown_s") and trial < args.trials:
                import time
                print(f"    (waiting {scenario['cooldown_s']}s for the rate-limit window)")
                time.sleep(scenario["cooldown_s"])

        rows.append({"scenario": scenario, "trials": trials})

    write_report(rows, args)


def write_report(rows, args):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"

    n = args.trials
    headers = " | ".join(f"Run {i}" for i in range(1, n + 1))
    divider = "|".join(["---"] * n)

    lines = [
        f"# Run log{f' — {args.label}' if args.label else ''}",
        "",
        "- Produced by: `run_eval.py::main`",
        "- Service: `app.py::submit` · scoring: `scoring.py::combine_signals`",
        f"- {n} trials per criterion · {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Fill in Target from `criteria.md`, and Run and Verdict from the output",
        "underneath. Whether a trial passed depends on the criterion you wrote.",
        "",
        f"| Criterion | Target | {headers} | Verdict |",
        f"|---|---|{divider}|---|",
    ]

    for row in rows:
        scenario = row["scenario"]
        number = scenario.get("criterion")
        name = f"{number}. {scenario['name']}" if number else scenario["name"]
        lines.append(f"| {name} |  | {' | '.join([' '] * n)} |  |")

    lines += ["", "---", "", "## What actually came back", "",
              "Real output. Paste the relevant parts into your README — the rubric",
              "asks for the actual JSON, not a description of it.", ""]

    for row in rows:
        scenario = row["scenario"]
        lines += [f"### {scenario['name']}", ""]
        for trial_number, results in enumerate(row["trials"], 1):
            lines += [f"**Trial {trial_number}**", "", "```json",
                      json.dumps(results, indent=2), "```", ""]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {path.relative_to(config.ROOT)}")
    print("Commit it. It's the evidence the test actually happened.")


if __name__ == "__main__":
    main()
