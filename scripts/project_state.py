#!/usr/bin/env python3
"""CLI for reading and validating ops/project-state.json. Standard library only."""

import json
import sys
from pathlib import Path

STATE_PATH = Path(__file__).resolve().parent.parent / "ops" / "project-state.json"

REQUIRED_KEYS = (
    "schema_version",
    "project",
    "state",
    "active_issue",
    "active_branch",
    "last_completed",
    "next_action",
    "blockers",
    "retry_counts",
    "last_verified_at",
)

VALID_STATES = (
    "IDLE",
    "PLANNING",
    "BRANCHING",
    "IMPLEMENTING",
    "QA_LOCAL",
    "PR_OPEN",
    "CI_CHECK",
    "REVIEW",
    "MERGE_READY",
    "MERGED",
    "DEPLOY_DISPATCH",
    "DEPLOY_VERIFY",
    "DONE",
    "REVIEW_NEEDED",
    "BLOCKED_HARD_GATE",
    "NEXT_ISSUE_SELECT",
)


def load_state(path=STATE_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(data, path=STATE_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def validate(data):
    errors = []

    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"missing required key: {key}")

    if "state" in data and data["state"] not in VALID_STATES:
        errors.append(f"invalid state: {data['state']!r} (expected one of {VALID_STATES})")

    if "next_action" in data:
        next_action = data["next_action"]
        if not isinstance(next_action, str) or not next_action.strip():
            errors.append("next_action must be a non-empty string")

    if "retry_counts" in data:
        retry_counts = data["retry_counts"]
        if not isinstance(retry_counts, dict):
            errors.append("retry_counts must be an object")
        else:
            for name, value in retry_counts.items():
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(f"retry_counts.{name} must be a non-negative integer")

    if "blockers" in data and not isinstance(data["blockers"], list):
        errors.append("blockers must be an array")

    return errors


def cmd_show(_args):
    data = load_state()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_validate(_args):
    data = load_state()
    errors = validate(data)
    if errors:
        for err in errors:
            print(f"INVALID: {err}", file=sys.stderr)
        return 1
    print("OK: project-state.json is valid")
    return 0


def cmd_set_next(args):
    if not args:
        print("usage: project_state.py set-next <next_action text>", file=sys.stderr)
        return 2
    next_action = " ".join(args).strip()
    if not next_action:
        print("ERROR: next_action must not be empty", file=sys.stderr)
        return 2
    data = load_state()
    data["next_action"] = next_action
    errors = validate(data)
    if errors:
        for err in errors:
            print(f"INVALID: {err}", file=sys.stderr)
        return 1
    save_state(data)
    print(f"OK: next_action set to {next_action!r}")
    return 0


COMMANDS = {
    "show": cmd_show,
    "validate": cmd_validate,
    "set-next": cmd_set_next,
}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        print(f"usage: project_state.py <{'|'.join(COMMANDS)}> [args...]", file=sys.stderr)
        return 2
    return COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
