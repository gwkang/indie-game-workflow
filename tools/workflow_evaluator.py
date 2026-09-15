"""Compare workflow traces with separately stored observable expectations."""
import argparse
import json
from pathlib import Path


def evaluate(results, expectations):
    actual = {row["caseId"]: row["trace"] for row in results}
    verdicts = []
    for case_id, expected in expectations.items():
        trace = actual.get(case_id)
        failures = [] if trace is not None else ["missing result"]
        if trace is not None:
            for key, value in expected.items():
                if trace.get(key) != value:
                    failures.append(f"{key}: expected {value!r}, got {trace.get(key)!r}")
        verdicts.append({
            "caseId": case_id,
            "status": "pass" if not failures else "fail",
            "failures": failures,
        })
    unknown = sorted(set(actual) - set(expectations))
    return {
        "status": "pass" if all(row["status"] == "pass" for row in verdicts) and not unknown else "fail",
        "cases": verdicts,
        "unknownCases": unknown,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--expectations", type=Path, required=True)
    args = parser.parse_args()
    verdict = evaluate(
        json.loads(args.results.read_text(encoding="utf-8"))["results"],
        json.loads(args.expectations.read_text(encoding="utf-8")),
    )
    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    raise SystemExit(0 if verdict["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
