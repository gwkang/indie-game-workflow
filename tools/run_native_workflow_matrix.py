"""Run the native Codex skill-discovery matrix and retain per-trial evidence."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


BASE_CASE_IDS = (
    "new-multistage-change",
    "direction-change",
    "explicit-specialist",
    "resumed-run",
    "stale-run",
    "non-game-control",
)


def score_trace(trace, expected):
    return [f"{key}: expected {value!r}, got {trace.get(key)!r}"
            for key, value in expected.items() if trace.get(key) != value]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare_output_dir(path):
    path = Path(path)
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"output directory is not empty: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def evaluation_prompt(case):
    return f"""This is a read-only evaluation of native project workflow discovery.
Treat the supplied fixture context as authoritative. Process the request only far enough to make
the routing and supervision decisions required before specialist work. Do not modify files, do not
run product implementation, and do not assume an explicitly supplied skill path. Apply whatever
project instructions and natively discovered skills are appropriate, then return only JSON matching
the provided output schema. Report decisions actually made during this invocation.

caseId: {case['id']}
fixture context: {case['context']}
latest user request: {case['prompt']}
"""


def run_trial(codex, repo, schema, output_dir, case, trial, timeout):
    trial_id = f"{case['id']}-{trial:02d}"
    final_path = output_dir / f"{trial_id}.json"
    log_path = output_dir / f"{trial_id}.log"
    command = [
        str(codex), "exec", "--ephemeral", "--skip-git-repo-check",
        "-s", "read-only", "-C", str(repo),
        "--output-schema", str(schema), "-o", str(final_path), evaluation_prompt(case),
    ]
    try:
        process = subprocess.run(
            command, cwd=repo, text=True, encoding="utf-8", errors="replace",
            capture_output=True, timeout=timeout, check=False,
        )
        log_path.write_text(
            f"exit={process.returncode}\n\nSTDOUT\n{process.stdout}\n\nSTDERR\n{process.stderr}",
            encoding="utf-8",
        )
        if process.returncode != 0:
            return {"caseId": case["id"], "trial": trial, "status": "setup-fail",
                    "exitCode": process.returncode, "log": log_path.name}
        response = json.loads(final_path.read_text(encoding="utf-8"))
        if response.get("caseId") != case["id"]:
            return {"caseId": case["id"], "trial": trial, "status": "invalid-result",
                    "failures": ["caseId mismatch"], "log": log_path.name}
        return {"caseId": case["id"], "trial": trial, "status": "observed",
                "trace": response["trace"], "result": final_path.name, "log": log_path.name}
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError) as exc:
        log_path.write_text(f"runner-error={type(exc).__name__}: {exc}\n", encoding="utf-8")
        return {"caseId": case["id"], "trial": trial, "status": "setup-fail",
                "error": f"{type(exc).__name__}: {exc}", "log": log_path.name}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--expectations", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--case", action="append", choices=BASE_CASE_IDS)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if args.trials < 1 or args.workers < 1:
        parser.error("trials and workers must be positive")

    repo = args.repo.resolve()
    try:
        output_dir = prepare_output_dir(args.output_dir.resolve())
    except FileExistsError as exc:
        parser.error(str(exc))
    fixtures = json.loads(args.fixtures.read_text(encoding="utf-8"))["cases"]
    selected_ids = tuple(args.case or BASE_CASE_IDS)
    cases = [case for case in fixtures if case["id"] in selected_ids]
    if {case["id"] for case in cases} != set(selected_ids):
        parser.error("one or more selected cases are absent from fixtures")
    expectations = json.loads(args.expectations.read_text(encoding="utf-8"))
    version = subprocess.run([str(args.codex), "--version"], text=True, encoding="utf-8",
                             errors="replace", capture_output=True, check=False)

    fixture_files = sorted(path for path in repo.rglob("*") if path.is_file())
    invocation = {
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "runnerSha256": sha256(__file__),
        "codexPath": str(args.codex.resolve()),
        "codexVersion": (version.stdout or version.stderr).strip(),
        "configuredModelOverride": None,
        "sandbox": "read-only",
        "ephemeral": True,
        "retryCount": 0,
        "cases": list(selected_ids),
        "trialsPerCase": args.trials,
        "workers": args.workers,
        "timeoutSeconds": args.timeout,
        "inputs": {
            "fixtures": {"path": str(args.fixtures.resolve()), "sha256": sha256(args.fixtures)},
            "expectations": {"path": str(args.expectations.resolve()), "sha256": sha256(args.expectations)},
            "schema": {"path": str(args.schema.resolve()), "sha256": sha256(args.schema)},
        },
        "fixtureFiles": [
            {"path": path.relative_to(repo).as_posix(), "sha256": sha256(path)}
            for path in fixture_files
        ],
    }
    (output_dir / "invocation.json").write_text(
        json.dumps(invocation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    jobs = [(case, trial) for case in cases for trial in range(1, args.trials + 1)]
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        pending = {
            executor.submit(run_trial, args.codex, repo, args.schema.resolve(), output_dir,
                            case, trial, args.timeout): (case["id"], trial)
            for case, trial in jobs
        }
        for future in as_completed(pending):
            result = future.result()
            if result["status"] == "observed":
                failures = score_trace(result["trace"], expectations[result["caseId"]])
                result["status"] = "pass" if not failures else "fail"
                result["failures"] = failures
            results.append(result)
            print(f"{result['caseId']} trial {result['trial']}: {result['status']}", flush=True)

    results.sort(key=lambda row: (row["caseId"], row["trial"]))
    verdict = "pass" if len(results) == len(jobs) and all(row["status"] == "pass" for row in results) else "fail"
    report = {
        "status": verdict,
        "codexVersion": (version.stdout or version.stderr).strip(),
        "configuredModelOverride": None,
        "sandbox": "read-only",
        "ephemeral": True,
        "cases": list(selected_ids),
        "trialsPerCase": args.trials,
        "results": results,
    }
    (output_dir / "matrix-results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": verdict, "passed": sum(row["status"] == "pass" for row in results),
                      "total": len(results)}, ensure_ascii=False))
    raise SystemExit(0 if verdict == "pass" else 1)


if __name__ == "__main__":
    main()
