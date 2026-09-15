#!/usr/bin/env python3
"""Offline checks for rank.py.

Ranking is advisory, so the properties worth pinning are not "this paper scores
47". They are the ones whose failure is silent: that nothing is ever dropped,
that the order is reproducible, that an on-topic paper outranks an off-topic one,
and that the reject flags stay sparse enough to be worth reading.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import rank as R  # noqa: E402

FAILURES: list[str] = []


def check(label: str, got, want) -> None:
    if got != want:
        FAILURES.append(f"{label}\n      got:  {got!r}\n      want: {want!r}")


def check_true(label: str, got) -> None:
    if not got:
        FAILURES.append(label)


CFG = R.load_config()
PROFILE = R.compile_profile(CFG)


def rec(ident: str, title: str, summary: str = "") -> dict:
    return {"id": ident, "title": title, "summary": summary, "url": f"https://arxiv.org/abs/{ident}"}


# --- the profile is derived from topics.toml, not hardcoded ------------------
check("every interest is compiled", len(PROFILE["interests"]), len(CFG["interests"]))
check_true("interests carry terms", all(e["terms"] for e in PROFILE["interests"]))
check_true(
    "reject terms exclude vocabulary shared with interests",
    not any(
        t for e in PROFILE["rejects"] for t in e["terms"]
        if any(t in i["terms"] for i in PROFILE["interests"])
    ),
)

# --- stopwords -------------------------------------------------------------
# "attack" and "security" are stripped deliberately: on a cs.CR feed they match
# everything, so leaving them in orders nothing.
check_true("generic security words are stopwords", "attack" in R.STOPWORDS and "security" in R.STOPWORDS)
check("stopwords and short tokens are dropped", R.terms("The attack is on a system"), set())
check_true("real topic words survive", "smuggling" in R.terms("HTTP request smuggling"))

# --- ordering ---------------------------------------------------------------
ON = rec("1", "Bypassing CFI and ASLR with a new heap exploitation primitive",
         "We demonstrate a kernel exploitation technique defeating pointer authentication.")
OFF = rec("2", "A Deep Learning Credit Risk Early Warning System",
          "We integrate multi-source heterogeneous data for credit scoring.")
WEB = rec("3", "HTTP request smuggling and desync between proxies and origins",
          "Parser discrepancies between CDNs and origin servers enable cache poisoning.")

scored_on = R.score(ON, PROFILE)
scored_off = R.score(OFF, PROFILE)
check_true("an in-scope paper scores above zero", scored_on["score"] > 0)
check_true("an off-topic paper scores at or below zero", scored_off["score"] <= 0)
check_true("in-scope outranks off-topic", scored_on["score"] > scored_off["score"])
check_true("a matching interest is named", any("mitigations" in m or "exploitation" in m
                                                for m in scored_on["matched"]))
check_true("web attack classes are recognised", R.score(WEB, PROFILE)["score"] > 0)

# --- title weighting --------------------------------------------------------
in_title = R.score(rec("4", "Fuzzing and symbolic execution for vulnerability discovery", "Unrelated body."), PROFILE)
in_body = R.score(rec("5", "Unrelated body.", "Fuzzing and symbolic execution for vulnerability discovery"), PROFILE)
check_true("a topic in the title outweighs the same topic in the abstract",
           in_title["score"] > in_body["score"])

# --- nothing is ever dropped ------------------------------------------------
records = [ON, OFF, WEB, rec("6", "", ""), rec("7", "Untitled")]
ordered = R.rank(records, PROFILE)
check("ranking returns every record it was given", len(ordered), len(records))
check("ranking preserves the id set", sorted(r["id"] for r in ordered), ["1", "2", "3", "6", "7"])
check_true("scores are non-increasing", all(
    ordered[i]["score"] >= ordered[i + 1]["score"] for i in range(len(ordered) - 1)
))
check_true("every record carries a score", all("score" in r for r in ordered))
check_true("the original record is not mutated", "score" not in ON)

# --- reproducibility --------------------------------------------------------
# Ties break on id, so two runs over the same input cannot disagree; an unstable
# order would make every regenerated brief look like a content change.
check("ranking is deterministic", [r["id"] for r in R.rank(records, PROFILE)],
      [r["id"] for r in ordered])
check("ties break on id",
      [r["id"] for r in R.rank([rec("9", "zzz"), rec("8", "zzz")], PROFILE)], ["8", "9"])

# --- empty and malformed input ----------------------------------------------
check("an empty input ranks to nothing", R.rank([], PROFILE), [])
check("a record with no title or summary scores zero", R.score(rec("6", "", ""), PROFILE)["score"], 0)
check("missing keys do not raise", R.score({"id": "x"}, PROFILE)["score"], 0)

# --- reject flags -----------------------------------------------------------
# A flag down-weights and is visible; it never removes the item. The threshold is
# two co-occurring discriminating terms because one ("detection") appears in a
# large share of cs.CR abstracts.
DETECT = rec("10", "A detection and mitigation design for intrusions",
             "We present a defence with no new attack result, evaluating our detection design.")
flagged = R.score(DETECT, PROFILE)
check_true("a defence-only paper is flagged", bool(flagged["flagged"]))
check_true("a flagged item is still returned", flagged in R.rank([DETECT], PROFILE))
check("one discriminating term alone does not flag", R.score(rec("11", "Detection"), PROFILE)["flagged"], [])
check("an in-scope paper is not flagged", scored_on["flagged"], [])
check("REJECT_MIN_TERMS is 2", R.REJECT_MIN_TERMS, 2)

if FAILURES:
    print(f"rank: FAILED ({len(FAILURES)}):\n")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("rank: all checks passed")
