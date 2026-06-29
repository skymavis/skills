# Promoting drafts — mechanics

Promotion turns a draft into an accepted decision. **An accepted decision must never reference a
draft** (a breach). When promoting a draft that references other drafts, each reference to a draft
*outside the promoted set* is one of:

| Reference                      | Direction | Resolution                                                                                   |
| :----------------------------- | :-------- | :------------------------------------------------------------------------------------------- |
| `relates_to` (front-matter)    | symmetric | **dereference** — drop here; the referenced draft gains your new counter in its `relates_to` |
| `superseded_by` (front-matter) | backward  | **dereference** — drop here; the referenced draft gains your new counter in its `supersedes` |
| `supersedes` → a draft         | forward   | **blocking** — promote that draft first                                                      |
| prose `` `DRFT` `` in the body | content   | **blocking** — promote that draft first                                                      |

`supersedes` → an existing **decision** is a real supersession, gated behind `--allow-replace`.

## What `promote` does

`promote <name…>` is advisory — it never silently promotes extras or rewrites refs:

| Situation                             | Result                                                                                                            |
| :------------------------------------ | :---------------------------------------------------------------------------------------------------------------- |
| self-contained                        | promotes it                                                                                                       |
| only **dereferenceable** refs         | refuses; re-run `promote <name…> --deref` (shows the moves)                                                       |
| any **blocking** ref                  | refuses; prints the minimal blocking set to co-promote (your draft highlighted) **and a copy-paste agent prompt** |
| `supersedes` an existing **decision** | refuses; re-run `promote <name…> --allow-replace`                                                                 |

- `promote <name…> --deref` inverts the dereferenceable edges, then promotes — refused if any
  blocking ref is present.
- `promote <name…> --allow-replace` confirms archiving the decisions the draft `supersedes` (the ids
  are shown in the preview, so the flag is just intent).
- Promote several at once, space- or comma-separated. Refs *within* the set become counter↔counter
  automatically.

**Invariant:** after any promotion, everything the promoted record pointed at refers back to it —
via the inverted edge (`--deref`) or a counter rewrite (co-promoted).
