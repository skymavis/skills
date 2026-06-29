#!/usr/bin/env python3
"""Validate SKILL.md contracts for every skill in this repo.

The single source of truth for what a valid skill looks like here. Locked to the
Agent Skills frontmatter contract (so authored skills stay portable/uploadable)
plus two repo-specific rules a generic linter wouldn't know:
  * the skill's folder name must equal its frontmatter `name`
  * relative links in SKILL.md must resolve

Usage:
    python scripts/validate_skills.py                 # validate every skill + the template
    python scripts/validate_skills.py path/to/SKILL.md [more...]

Exit 0 if all pass, 1 if any fail. Dependency-free (no PyYAML).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
REQUIRED_KEYS = {"name", "description"}
RESERVED_NAMES = {"anthropic", "claude"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")  # kebab-case, no leading/trailing/double hyphen
NAME_MAX = 64
DESC_MAX = 1024
BODY_MAX_LINES = 500
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")  # markdown links (not images)
ROOT = Path(__file__).resolve().parent.parent


def _indent(s: str) -> int:
    return len(s) - len(s.lstrip(" "))


def parse_frontmatter(text: str) -> tuple[dict | None, str | None]:
    """Tiny YAML-frontmatter reader (no PyYAML): top-level `key: value`, block
    scalars (`>`, `>-`, `|`, `|-`), and nested mapping/list blocks under a key —
    the nested children are captured (so the key counts as present) rather than
    flattened into top-level keys. Enough to enforce the contract; returns
    (data, error). Scalar values are str; nested blocks are list[str]."""
    if not text.startswith("---"):
        return None, "missing frontmatter: file must start with a '---' fence"
    end = text.find("\n---", 3)
    if end == -1:
        return None, "frontmatter not closed with a '---' line"
    lines = text[3:end].split("\n")
    data: dict = {}
    i, n = 0, len(lines)
    while i < n:
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        if "\t" in raw[: _indent(raw)]:
            return None, f"frontmatter uses a tab for indentation (line {i + 1}); use spaces"
        if _indent(raw) != 0:
            return None, f"unexpected indentation in frontmatter (line {i + 1}): {raw!r}"
        if ":" not in raw:
            return None, f"frontmatter line is not `key: value` (line {i + 1}): {raw!r}"
        key, _, val = raw.partition(":")
        key, val = key.strip(), val.strip()
        if key in data:
            return None, f"duplicate frontmatter key {key!r} (line {i + 1})"
        if val in (">", ">-", ">+", "|", "|-", "|+"):  # block scalar
            parts, j = [], i + 1
            while j < n and (lines[j].strip() == "" or _indent(lines[j]) > 0):
                parts.append(lines[j].strip())
                j += 1
            data[key] = ("\n" if val[0] == "|" else " ").join(parts).strip()
            i = j
        elif val == "":  # nested map/list (or empty)
            child, j = [], i + 1
            while j < n and (lines[j].strip() == "" or _indent(lines[j]) > 0):
                if lines[j].strip():
                    child.append(lines[j].strip())
                j += 1
            data[key] = child if child else ""  # present; not flattened
            i = j
        else:  # scalar
            data[key] = val.strip().strip('"').strip("'")
            i += 1
    return data, None


def validate_one(skill_md: Path) -> list[str]:
    errs: list[str] = []
    where = skill_md.relative_to(ROOT) if skill_md.is_relative_to(ROOT) else skill_md
    text = skill_md.read_text(encoding="utf-8")
    data, perr = parse_frontmatter(text)
    if perr:
        return [f"{where}: {perr}"]

    extra = set(data) - ALLOWED_KEYS
    if extra:
        errs.append(f"{where}: disallowed frontmatter key(s): {', '.join(sorted(extra))}")
    for k in sorted(REQUIRED_KEYS - set(data)):
        errs.append(f"{where}: missing required key '{k}'")

    name = data.get("name", "")
    if "name" in data and not isinstance(name, str):
        errs.append(f"{where}: name must be a single scalar value")
        name = ""
    if name:
        folder = skill_md.parent.name
        if name != folder:
            errs.append(f"{where}: name {name!r} must equal folder name {folder!r}")
        if len(name) > NAME_MAX:
            errs.append(f"{where}: name longer than {NAME_MAX} chars")
        if not NAME_RE.match(name):
            errs.append(
                f"{where}: name {name!r} must be kebab-case [a-z0-9-] "
                "with no leading/trailing/double hyphen"
            )
        if name in RESERVED_NAMES:
            errs.append(f"{where}: name {name!r} is reserved")

    if "description" in data:
        desc = data["description"]
        if not isinstance(desc, str):
            errs.append(f"{where}: description must be a single scalar value")
        else:
            if not desc.strip():
                errs.append(f"{where}: description is empty")
            if len(desc) > DESC_MAX:
                errs.append(f"{where}: description longer than {DESC_MAX} chars ({len(desc)})")
            if "<" in desc or ">" in desc:
                errs.append(f"{where}: description must not contain angle brackets (< or >)")

    body = text[text.find("\n---", 3) + 4 :]
    n = len(body.strip("\n").split("\n"))
    if n > BODY_MAX_LINES:
        errs.append(f"{where}: SKILL.md body is {n} lines (budget {BODY_MAX_LINES})")

    for target in LINK_RE.findall(body):
        t = target.split("#", 1)[0].strip()
        if (
            not t
            or re.match(r"[a-z][a-z0-9+.-]*://", t)
            or t.startswith("mailto:")
            or t.startswith("/")
        ):
            continue
        if not (skill_md.parent / t).exists():
            errs.append(f"{where}: broken relative link -> {target}")
    return errs


def discover() -> list[Path]:
    found = sorted((ROOT / "skills").glob("*/SKILL.md"))
    found += sorted((ROOT / "template").glob("*/SKILL.md"))
    return found


def main(argv: list[str]) -> int:
    targets = [Path(a).resolve() for a in argv] or discover()
    if not targets:
        print("no SKILL.md files found", file=sys.stderr)
        return 1
    errs: list[str] = []
    for p in targets:
        if not p.exists():
            errs.append(f"{p}: not found")
            continue
        errs.extend(validate_one(p))
    if errs:
        print("\n".join(errs), file=sys.stderr)
        print(f"\n{len(errs)} problem(s) across {len(targets)} SKILL.md", file=sys.stderr)
        return 1
    print(f"ok: {len(targets)} SKILL.md valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
