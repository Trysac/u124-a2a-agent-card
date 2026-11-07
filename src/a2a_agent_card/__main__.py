"""CLI entry point for a2a_agent_card."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import MAX_INPUT_BYTES, validate_card


def main(argv: Sequence[str] | None = None) -> int:
    """Run CLI commands: validate <file>."""
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] != "validate":
        sys.stderr.write("Usage: python -m a2a_agent_card validate <file>\n")
        return 2

    if len(args) != 2:
        sys.stderr.write("Error: 'validate' command requires exactly one file path argument.\n")
        return 2

    file_path = Path(args[1])
    try:
        if not file_path.is_file():
            sys.stderr.write(f"File not found: {file_path}\n")
            return 2
        file_size = file_path.stat().st_size
        if file_size > MAX_INPUT_BYTES:
            sys.stderr.write(f"File size exceeds maximum limit of {MAX_INPUT_BYTES} bytes\n")
            return 2
        content = file_path.read_text(encoding="utf-8")
        card = json.loads(content)
    except Exception as exc:
        sys.stderr.write(f"Parse or I/O error: {exc}\n")
        return 2

    issues = validate_card(card)
    if not issues:
        sys.stdout.write("ok\n")
        return 0

    has_error = False
    for issue in issues:
        sys.stdout.write(f"{issue.severity} {issue.path} {issue.code}\n")
        if issue.severity == "error":
            has_error = True

    if not has_error:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
