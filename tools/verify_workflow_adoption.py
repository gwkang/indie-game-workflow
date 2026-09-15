"""Verify exact core parity and an exhaustive project-override allowlist."""
import argparse
import hashlib
import json
from pathlib import Path


class VerificationError(ValueError):
    pass


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def inventory(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in root.rglob("*")
            if p.is_file() and p.name != "workflow-adoption.lock.json"}


def verify(repo, lock_path):
    repo = Path(repo).resolve()
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    if lock.get("schemaVersion") != 1:
        raise VerificationError("unsupported adoption lock")
    source = repo / lock["sourceRoot"]
    adopted = repo / lock["adoptedRoot"]
    source_files, adopted_files = inventory(source), inventory(adopted)
    core = {row["path"]: row["sha256"] for row in lock["coreFiles"]}
    overrides = {row["path"]: row for row in lock["overrides"]}
    if set(core).intersection(overrides):
        raise VerificationError("core paths cannot be overrides")
    for path, expected in core.items():
        if source_files.get(path) != expected or adopted_files.get(path) != expected:
            raise VerificationError(f"core mismatch: {path}")
    actual_differences = {path for path in set(source_files) | set(adopted_files)
                          if source_files.get(path) != adopted_files.get(path)}
    if actual_differences != set(overrides):
        raise VerificationError("override list is not exhaustive and exact")
    for path, row in overrides.items():
        if source_files.get(path) != row["sourceSha256"] or adopted_files.get(path) != row["adoptedSha256"]:
            raise VerificationError(f"override drift: {path}")
        if not row.get("owner") or not row.get("reason"):
            raise VerificationError(f"override lacks ownership: {path}")
    skill_files = sorted(adopted.glob("*/SKILL.md"))
    uncovered = []
    for skill_file in skill_files:
        content = skill_file.read_text(encoding="utf-8")
        if "role-contract.md" not in content and "WORKFLOW_ADOPTION.md" not in content:
            uncovered.append(skill_file.parent.name)
    if uncovered:
        raise VerificationError(f"skills lack shared workflow preflight: {', '.join(uncovered)}")
    return {
        "status": "pass",
        "coreFiles": len(core),
        "overrides": len(overrides),
        "preflightCoveredSkills": len(skill_files),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lock", type=Path)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.repo, args.lock), indent=2))
    except (VerificationError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
