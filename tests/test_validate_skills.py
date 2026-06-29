"""Tests for scripts/validate_skills.py — the SKILL.md contract validator."""

import validate_skills


def write_skill(tmp_path, folder, frontmatter, body="# Title\n\nbody\n"):
    d = tmp_path / folder
    d.mkdir(parents=True, exist_ok=True)
    p = d / "SKILL.md"
    p.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return p


def ok(p):
    return validate_skills.validate_one(p) == []


# ── valid shapes ─────────────────────────────────────────────────────────────
def test_minimal_valid(tmp_path):
    p = write_skill(
        tmp_path, "foo-bar", "name: foo-bar\ndescription: Does a thing. Use when needed."
    )
    assert ok(p)


def test_folded_block_scalar_description(tmp_path):
    p = write_skill(
        tmp_path, "foo", "name: foo\ndescription: >-\n  Folded line one\n  folded line two."
    )
    assert ok(p)


def test_nested_metadata_map_allowed(tmp_path):
    # regression: nested metadata/compatibility maps are allowed and must NOT be
    # flattened into disallowed top-level keys.
    fm = (
        "name: foo\ndescription: Does X. Use when Y.\n"
        'metadata:\n  version: "1.0"\n  author: jane\n'
        "compatibility:\n  platforms:\n    - linux"
    )
    p = write_skill(tmp_path, "foo", fm)
    assert ok(p), validate_skills.validate_one(p)


def test_allowed_tools_list(tmp_path):
    p = write_skill(
        tmp_path, "foo", "name: foo\ndescription: D. Use when.\nallowed-tools:\n  - Read\n  - Write"
    )
    assert ok(p)


# ── rejections ───────────────────────────────────────────────────────────────
def test_disallowed_key(tmp_path):
    p = write_skill(tmp_path, "foo", "name: foo\ndescription: d\nbogus: x")
    assert not ok(p)


def test_name_must_match_folder(tmp_path):
    p = write_skill(tmp_path, "foo", "name: bar\ndescription: d")
    assert not ok(p)


def test_missing_description(tmp_path):
    p = write_skill(tmp_path, "foo", "name: foo")
    assert not ok(p)


def test_angle_brackets_in_description(tmp_path):
    p = write_skill(tmp_path, "foo", "name: foo\ndescription: replace <name> here")
    assert not ok(p)


def test_bad_name_chars(tmp_path):
    p = write_skill(tmp_path, "Foo_Bar", "name: Foo_Bar\ndescription: d")
    assert not ok(p)


def test_reserved_name(tmp_path):
    p = write_skill(tmp_path, "claude", "name: claude\ndescription: d")
    assert not ok(p)


def test_body_over_budget(tmp_path):
    body = "# T\n" + "\n".join(f"line {i}" for i in range(validate_skills.BODY_MAX_LINES + 5))
    p = write_skill(tmp_path, "foo", "name: foo\ndescription: d", body=body)
    assert not ok(p)


def test_duplicate_key_rejected(tmp_path):
    p = write_skill(tmp_path, "foo", "name: foo\nname: foo\ndescription: d")
    assert not ok(p)


def test_unclosed_frontmatter(tmp_path):
    d = tmp_path / "foo"
    d.mkdir()
    (d / "SKILL.md").write_text("---\nname: foo\ndescription: d\n\n# no close\n", encoding="utf-8")
    assert not ok(d / "SKILL.md")


def test_broken_relative_link(tmp_path):
    p = write_skill(
        tmp_path,
        "foo",
        "name: foo\ndescription: d",
        body="# T\n\nSee [docs](references/missing.md).\n",
    )
    assert not ok(p)


def test_main_cli_pass_and_fail(tmp_path):
    good = write_skill(tmp_path, "good", "name: good\ndescription: ok. use when.")
    bad = write_skill(tmp_path, "bad", "name: mismatch\ndescription: d")
    assert validate_skills.main([str(good)]) == 0
    assert validate_skills.main([str(bad)]) == 1
