"""
Tests for scripts/decisions.py — the decision-records registry tool.

Option B: the tool takes an injectable `root` (the docs/ dir), so every test runs
against a synthetic tree under tmp_path and never touches the real repo.
"""

import decisions
import pytest


# ── fixture helpers ─────────────────────────────────────────────────────────
def record_text(
    counter,
    typ,
    title,
    *,
    body="",
    status="accepted",
    relates_to="[]",
    supersedes="null",
    superseded_by="null",
    summary="one-line summary",
    tags="[]",
):
    return (
        f'---\nid: "{counter}"\ntitle: {title}\ntype: {typ}\nstatus: {status}\n'
        f"summary: {summary}\ntags: {tags}\nrelates_to: {relates_to}\n"
        f"supersedes: {supersedes}\nsuperseded_by: {superseded_by}\n---\n\n"
        f"# {counter} — {title}\n\n{body}\n"
    )


def place(root, counter, typ, title, *, lifecycle="decisions", subdir=None, **kw):
    d = (
        root / "decisions" / "accepted" / (subdir or typ)
        if lifecycle == "decisions"
        else root / "decisions" / lifecycle
    )
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{counter}-{title}.md"
    p.write_text(record_text(counter, typ, title, **kw), encoding="utf-8")
    return p


def place_draft(
    root,
    did,
    typ,
    title,
    *,
    status="draft",
    relates_to="[]",
    supersedes="null",
    superseded_by="null",
    body="",
):
    d = root / "decisions" / "drafts"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{did}-{title}.md"
    p.write_text(
        f"---\nid: {did}\ntitle: {title}\ntype: {typ}\nstatus: {status}\n"
        f"relates_to: {relates_to}\nsupersedes: {supersedes}\nsuperseded_by: {superseded_by}\n"
        f"---\n\n# {did} — {title}\n\n{body}\n",
        encoding="utf-8",
    )
    return p


def write_threat_model(root, body):
    root.mkdir(parents=True, exist_ok=True)
    (root / "threat-model.md").write_text(f"# Threat Model\n\n{body}\n", encoding="utf-8")


@pytest.fixture
def root(tmp_path):
    """docs/ with contiguous accepted 0001..0003; 0003 (security) cites 0001 & 0002."""
    docs = tmp_path / "docs"
    place(docs, "0001", "architecture", "alpha")
    place(docs, "0002", "architecture", "beta")
    place(docs, "0003", "security", "gamma", body="builds on `0001` and `0002`.")
    return docs


@pytest.fixture
def built(root):
    assert decisions.main(["build", "--relink"], root=root) == 0
    return root


# ── build / render ──────────────────────────────────────────────────────────
def test_build_writes_index_sorted(root):
    assert decisions.main(["build"], root=root) == 0
    index = (root / "decisions" / "INDEX.md").read_text()
    assert index.index("0001") < index.index("0002") < index.index("0003")
    assert "(accepted/architecture/0001-alpha.md)" in index
    assert "| architecture |" in index and "| security |" in index


def test_index_empty_when_no_decisions(tmp_path):
    docs = tmp_path / "docs"
    place_draft(docs, "ABCD", "security", "wip")
    assert decisions.main(["build"], root=docs) == 0
    assert "no decisions yet" in (docs / "decisions" / "INDEX.md").read_text()


def test_no_proposed_status_allowed(root):
    place(root, "0004", "architecture", "wip", status="proposed")
    assert decisions.main(["check"], root=root) == 1


# ── relink ──────────────────────────────────────────────────────────────────
def test_relink_cross_directory(built):
    body = (built / "decisions/accepted/security/0003-gamma.md").read_text()
    assert "[`0001`](../architecture/0001-alpha.md)" in body


def test_relink_idempotent(built):
    p = built / "decisions/accepted/security/0003-gamma.md"
    before = p.read_text()
    assert decisions.main(["build", "--relink"], root=built) == 0
    assert p.read_text() == before


def test_move_self_heals(built):
    src = built / "decisions/accepted/architecture/0001-alpha.md"
    src.rename(src.with_name("0001-alpha-renamed.md"))
    assert decisions.main(["check"], root=built) == 1
    assert decisions.main(["build", "--relink"], root=built) == 0
    assert decisions.main(["check"], root=built) == 0
    gamma = (built / "decisions/accepted/security/0003-gamma.md").read_text()
    assert "0001-alpha-renamed.md" in gamma


# ── drafts: UPPERCASE ids, draft↔draft links ────────────────────────────────
def test_draft_to_draft_link(root):
    place_draft(root, "AAAA", "security", "one")
    place_draft(root, "BBBB", "architecture", "two", body="relates to `AAAA`.")
    assert decisions.main(["build", "--relink"], root=root) == 0
    assert "[`AAAA`](AAAA-one.md)" in (root / "decisions/drafts/BBBB-two.md").read_text()


def test_lowercase_draft_id_rejected(built):
    place_draft(built, "abcd", "security", "lower")
    assert decisions.main(["check"], root=built) == 1


def test_draft_requires_4letter_id(built):
    place_draft(built, "AB", "security", "shorty")
    assert decisions.main(["check"], root=built) == 1


def test_draft_duplicate_id(built):
    place_draft(built, "ABCD", "security", "one")
    place_draft(built, "ABCD", "architecture", "two")
    assert decisions.main(["check"], root=built) == 1


# ── threat-model.md in the link system ──────────────────────────────────────
def test_threat_model_gets_linked(built):
    write_threat_model(built, "Vector X addressed by `0001`.")
    assert decisions.main(["build", "--relink"], root=built) == 0
    link = "[`0001`](decisions/accepted/architecture/0001-alpha.md)"
    assert link in (built / "threat-model.md").read_text()
    assert decisions.main(["check"], root=built) == 0


def test_threat_model_broken_ref_flagged(built):
    write_threat_model(built, "Addressed by `0099`.")
    assert decisions.main(["check"], root=built) == 1


def test_any_doc_is_linked_and_checked(built):
    (built / "roadmap.md").write_text(
        "# Roadmap\n\nMilestone builds on `0001`.\n", encoding="utf-8"
    )
    assert decisions.main(["build", "--relink"], root=built) == 0
    link = "[`0001`](decisions/accepted/architecture/0001-alpha.md)"
    assert link in (built / "roadmap.md").read_text()
    (built / "roadmap.md").write_text("# Roadmap\n\nBuilds on `0099`.\n", encoding="utf-8")
    assert decisions.main(["check"], root=built) == 1


def test_templates_and_index_excluded_from_linkcheck(built):
    (built / "_scratch.md").write_text(
        "# scratch\n\nrefs `0099`.\n", encoding="utf-8"
    )  # _-prefixed
    assert decisions.main(["check"], root=built) == 0  # excluded, so its bad ref is ignored


# ── placement, duplicates, skips ────────────────────────────────────────────
def test_dir_must_match_type(root):
    place(root, "0004", "architecture", "misplaced", subdir="security")
    assert decisions.main(["check"], root=root) == 1


def test_custom_type_is_open(built):
    place_draft(built, "LEGL", "legal", "retention-policy")  # a type outside the usual set
    assert decisions.main(["promote", "LEGL"], root=built) == 0
    # the type's dir is auto-created on promotion
    assert (built / "decisions/accepted/legal/0004-retention-policy.md").exists()
    assert decisions.main(["check"], root=built) == 0


def test_invalid_type_slug_rejected(built):
    place_draft(built, "ABCD", "Security", "bad-slug")  # uppercase -> not a slug
    assert decisions.main(["check"], root=built) == 1


def test_new_type_warns_but_passes(built, capsys):
    place_draft(built, "LEGL", "legal", "thing")  # no decisions/legal/ yet
    assert decisions.main(["check"], root=built) == 0  # non-blocking
    assert "new type" in capsys.readouterr().err  # but warned


def test_archived_status_must_be_retired(root):
    place(root, "0004", "architecture", "notretired", lifecycle="archived", status="accepted")
    assert decisions.main(["check"], root=root) == 1


def test_superseded_in_archived_ok(built):
    place(built, "0004", "architecture", "retired", lifecycle="archived", status="superseded")
    assert decisions.main(["build", "--relink"], root=built) == 0
    assert decisions.main(["check"], root=built) == 0


def test_duplicate_counter(root):
    place(root, "0001", "security", "clash")
    assert decisions.main(["check"], root=root) == 1


def test_gap_in_counters(root):
    place(root, "0005", "architecture", "skipper")
    assert decisions.main(["check"], root=root) == 1


# ── decision → draft breach ─────────────────────────────────────────────────
def test_decision_referencing_draft_is_breach(built):
    place(built, "0004", "architecture", "leaky", body="depends on `WXYZ`.")
    place_draft(built, "WXYZ", "security", "candidate")
    assert decisions.main(["check"], root=built) == 1


def test_decision_relates_to_draft_is_breach(built):
    place(built, "0004", "architecture", "leaky2", relates_to='["WXYZ"]')
    place_draft(built, "WXYZ", "security", "candidate")
    assert decisions.main(["check"], root=built) == 1


def test_decision_linked_draft_ref_is_breach(built):
    # After relink a body ref becomes a markdown LINK; it must STILL be a breach, not only
    # bare inline-code refs (regression guard for the linked-ref blind spot).
    place_draft(built, "WXYZ", "security", "candidate")
    place(built, "0004", "architecture", "leaky3", body="builds on `WXYZ`.")
    assert decisions.main(["build", "--relink"], root=built) == 0  # refresh INDEX + linkify the ref
    body = (built / "decisions/accepted/architecture/0004-leaky3.md").read_text()
    assert "[`WXYZ`](" in body  # ref is now a markdown link
    assert decisions.main(["check"], root=built) == 1  # ...and is still flagged


# ── rename-draft-id ─────────────────────────────────────────────────────────
def test_rename_draft_repoints_refs(built):
    place_draft(built, "ABCD", "security", "target")
    place_draft(
        built, "EFGH", "architecture", "referrer", relates_to='["ABCD"]', body="depends on `ABCD`."
    )
    assert decisions.main(["rename-draft-id", "ABCD", "ZZZZ"], root=built) == 0
    ref = (built / "decisions/drafts/EFGH-referrer.md").read_text()
    assert "ZZZZ" in ref and "ABCD" not in ref
    assert decisions.main(["check"], root=built) == 0


def test_rename_draft_auto_uppercases(built):
    place_draft(built, "ABCD", "security", "thing")
    dest, err = decisions.rename_draft(built, "ABCD", "wxyz")
    assert err is None and dest.name == "WXYZ-thing.md"


def test_rename_draft_rejects_conflict(built):
    place_draft(built, "AAAA", "security", "one")
    place_draft(built, "BBBB", "architecture", "two")
    assert decisions.main(["rename-draft-id", "AAAA", "BBBB"], root=built) == 1


def test_rename_draft_rejects_invalid_id(built):
    place_draft(built, "AAAA", "security", "one")
    dest, err = decisions.rename_draft(built, "AAAA", "AB12")
    assert dest is None and err


# ── promote: single, closure/breach, multi, cycle ───────────────────────────
def test_promote_assigns_next_counter_accepted(built):
    place_draft(built, "QWER", "security", "new-idea")
    assert decisions.main(["promote", "QWER"], root=built) == 0
    dest = built / "decisions/accepted/security/0004-new-idea.md"
    assert dest.exists()
    assert 'id: "0004"' in dest.read_text() and "status: accepted" in dest.read_text()
    assert not (built / "decisions/drafts/QWER-new-idea.md").exists()
    assert decisions.main(["check"], root=built) == 0


def test_promote_rewrites_inbound_refs(built):
    place_draft(built, "ABCD", "security", "target")
    place_draft(
        built, "EFGH", "architecture", "referrer", relates_to='["ABCD"]', body="depends on `ABCD`."
    )
    assert decisions.main(["promote", "ABCD"], root=built) == 0
    ref = (built / "decisions/drafts/EFGH-referrer.md").read_text()
    assert "`0004`" in ref and "ABCD" not in ref
    assert decisions.main(["check"], root=built) == 0


def test_promote_breach_refused_with_closure(built):
    place_draft(built, "ABCD", "security", "needs-dep", body="see `EFGH`.")
    place_draft(built, "EFGH", "architecture", "dep")
    # promoting ABCD alone would leave a decision pointing at draft EFGH -> refused
    dests, err = decisions.promote(built, ["ABCD"])
    assert dests is None and err
    assert "EFGH" in err and "ABCD" in err and "requested" in err
    assert decisions.main(["promote", "ABCD"], root=built) == 1


def test_promote_closed_set_succeeds(built):
    place_draft(built, "ABCD", "security", "a", body="see `EFGH`.")
    place_draft(built, "EFGH", "architecture", "b")
    assert decisions.main(["promote", "ABCD", "EFGH"], root=built) == 0
    assert not list((built / "decisions" / "drafts").glob("[A-Z]*.md"))  # both consumed
    assert decisions.main(["check"], root=built) == 0  # no decision -> draft


def test_promote_cycle_needs_both(built):
    place_draft(built, "ABCD", "security", "a", body="see `EFGH`.")
    place_draft(built, "EFGH", "architecture", "b", body="see `ABCD`.")
    assert decisions.main(["promote", "ABCD"], root=built) == 1  # cycle -> breach
    assert decisions.main(["promote", "ABCD", "EFGH"], root=built) == 0  # together works
    assert decisions.main(["check"], root=built) == 0


def test_promote_comma_separated(built):
    place_draft(built, "ABCD", "security", "a", body="see `EFGH`.")
    place_draft(built, "EFGH", "architecture", "b")
    assert decisions.main(["promote", "ABCD,EFGH"], root=built) == 0
    assert decisions.main(["check"], root=built) == 0


def test_promote_disambiguates(built):
    place_draft(built, "QWER", "architecture", "alpha-cand")
    place_draft(built, "QWES", "security", "beta-cand")
    dests, err = decisions.promote(built, ["qwe"], input_fn=lambda _: "1")
    assert err is None and dests[0].name == "0004-alpha-cand.md"


def test_promote_no_match(built):
    assert decisions.main(["promote", "ZZZZ"], root=built) == 1


# ── deref / blocking / replace ──────────────────────────────────────────────
def test_promote_deref_inverts_frontmatter_edge(built):
    place_draft(built, "AAAA", "architecture", "alpha", relates_to='["BBBB"]')
    place_draft(built, "BBBB", "security", "beta")
    dests, err = decisions.promote(built, ["AAAA"])  # front-matter-only ref
    assert dests is None and "--deref" in err
    assert decisions.main(["promote", "--deref", "AAAA"], root=built) == 0
    assert (built / "decisions/accepted/architecture/0004-alpha.md").exists()
    assert '"0004"' in (built / "decisions/drafts/BBBB-beta.md").read_text()  # link moved onto BBBB
    assert decisions.main(["check"], root=built) == 0


def test_promote_deref_inverts_superseded_by_edge(built):
    # superseded_by is a scalar edge: inverting it must set BBBB's *single* `supersedes`
    # counter, not coerce it into a list (which would crash check on the unhashable value).
    place_draft(built, "AAAA", "architecture", "alpha", superseded_by='"BBBB"')
    place_draft(built, "BBBB", "security", "beta")
    dests, err = decisions.promote(built, ["AAAA"])  # front-matter-only ref
    assert dests is None and "--deref" in err
    assert decisions.main(["promote", "--deref", "AAAA"], root=built) == 0
    assert (built / "decisions/accepted/architecture/0004-alpha.md").exists()
    bbbb = decisions.parse_front_matter((built / "decisions/drafts/BBBB-beta.md").read_text())
    assert bbbb["supersedes"] == "0004"  # scalar counter, not a list
    assert decisions.main(["check"], root=built) == 0


def test_prose_ref_blocks_and_beats_deref(built):
    place_draft(built, "AAAA", "architecture", "alpha", relates_to='["BBBB"]', body="see `BBBB`.")
    place_draft(built, "BBBB", "security", "beta")
    dests, err = decisions.promote(built, ["AAAA"])
    assert dests is None and "blocked" in err and "--deref" not in err  # blocking wins


def test_deref_rejected_when_blocking(built):
    place_draft(built, "AAAA", "architecture", "alpha", body="see `BBBB`.")
    place_draft(built, "BBBB", "security", "beta")
    assert decisions.main(["promote", "--deref", "AAAA"], root=built) == 1


def test_supersedes_decision_needs_replace_then_archives(built):
    place_draft(built, "CCCC", "architecture", "newer", supersedes='"0001"')
    assert decisions.main(["promote", "CCCC"], root=built) == 1  # needs --allow-replace
    assert decisions.main(["promote", "CCCC", "--allow-replace"], root=built) == 0
    archived = built / "decisions/archived/0001-alpha.md"
    assert archived.exists() and "superseded" in archived.read_text()
    assert decisions.main(["check"], root=built) == 0


# ── check semantics & CLI ───────────────────────────────────────────────────
def test_check_clean(built):
    assert decisions.main(["check"], root=built) == 0


def test_check_read_only(built):
    p = built / "decisions/accepted/security/0003-gamma.md"
    before = (p.read_text(), (built / "decisions" / "INDEX.md").read_text())
    assert decisions.main(["check"], root=built) == 0
    assert (p.read_text(), (built / "decisions" / "INDEX.md").read_text()) == before


def test_check_detects_stale_index(built):
    p = built / "decisions/accepted/architecture/0001-alpha.md"
    p.write_text(p.read_text().replace("one-line summary", "changed"))
    assert decisions.main(["check"], root=built) == 1


def test_bare_relink_folds_into_build(root):
    assert decisions.main(["--relink"], root=root) == 0
    assert "[`0001`]" in (root / "decisions/accepted/security/0003-gamma.md").read_text()


def test_unknown_subcommand_exits_2(root):
    with pytest.raises(SystemExit) as e:
        decisions.main(["bogus"], root=root)
    assert e.value.code == 2


def test_relink_not_valid_on_check(root):
    with pytest.raises(SystemExit) as e:
        decisions.main(["check", "--relink"], root=root)
    assert e.value.code == 2


def test_promote_requires_query(root):
    with pytest.raises(SystemExit) as e:
        decisions.main(["promote"], root=root)
    assert e.value.code == 2


def test_rename_requires_two_args(root):
    with pytest.raises(SystemExit) as e:
        decisions.main(["rename-draft-id", "ABCD"], root=root)
    assert e.value.code == 2


def test_install_scaffolds_fresh_repo(tmp_path):
    decisions.install(tmp_path)  # repo root = tmp_path (no upward search)
    docs = tmp_path / "docs"
    assert (tmp_path / "scripts" / "decisions.py").is_symlink()
    for p in (
        "decisions/accepted/.gitkeep",
        "decisions/archived/.gitkeep",
        "decisions/README.md",
        "decisions/AGENTS.md",
        "decisions/_template.md",
        "decisions/drafts/_template.md",
        "decisions/INDEX.md",
    ):
        assert (docs / p).exists(), p
    assert decisions.main(["check"], root=docs) == 0  # scaffolded repo is valid immediately
    decisions.install(tmp_path)  # idempotent re-run doesn't raise
