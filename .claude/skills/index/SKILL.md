---
name: index
description: Create, update or check the INDEX.md that every folder in quant_cn must contain (CODING_STANDARD §5.1). Use after adding, renaming, moving or deleting any file or folder, when the user asks "what is in this folder", "update the index", or before marking a plan phase done. The indexes form a tree from the root INDEX.md down to every leaf folder.
---

# index

Every folder at every depth has an `INDEX.md`, including sub-packages, test subfolders and skill folders;
the only exceptions are the ignored paths below. The root `INDEX.md` lists top-level folders and files; each
folder's index lists its own subfolders (linking to their `INDEX.md`) and files. A folder row in a parent
index is invalid unless the child `INDEX.md` exists. Together they form a tree a
reader can walk without opening code.

## Format (fixed; `lint_contracts.py` parses it)

```markdown
# <folder path from repo root>/

<One line: what this folder is for and which layer it belongs to, if a package.>

## Folders
| Folder | Purpose |
|---|---|
| [`core/`](core/INDEX.md) | L1 base classes, config, exceptions, codecs |

## Files
| File | Purpose | Contains |
|---|---|---|
| `price_loader.py` | load daily bars from the lake | `PriceLoader` |
| `conftest.py` | shared fixtures: mini lake in tmp_path | `mini_lake`, `fake_client` |
```

Rules:
- Purpose is one line, imperative or noun phrase, no trailing period, no repetition of the file name.
- `Contains` lists classes for `.py` files (public functions only in `core/utils`), fixture names for
  `conftest.py`, top-level headings or the plan number for `.md`, dataset keys for YAML. Empty for
  files that hold nothing nameable (e.g. `.gitignore`).
- Both tables are sorted alphabetically. Omit an empty table.
- Lake folders under `data/` are not hand-indexed: `LakeCatalog.write_indexes()` generates theirs (plan 01 phase 3).
- `INDEX.md` itself is never listed. Ignored entirely: `data/`, `.venv/`, `__pycache__/`, `.git/`,
  `*.egg-info/`, `research_space/**/outputs/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.DS_Store`.
- The `Contains` column must agree with the class registry (same class names) and with the code.

## Modes

### Update (same change set as the file change)
1. For every file or folder added, renamed, moved or removed: edit the `INDEX.md` of its parent folder.
2. New folder: create its `INDEX.md` first, then add the folder row to the parent's index.
3. Removed folder: delete its index and the parent's row.
4. A class added to or removed from a `.py` file changes that file's `Contains` cell.

### Check
Run from repo root; report paths only.
```bash
python scripts/lint_contracts.py --index      # once it exists (plan 01 phase 1)
```
Until then, manual check:
```bash
find . -type d \( -name data -o -name .venv -o -name __pycache__ -o -name .git -o -name outputs -o -name '*cache*' \) -prune -o -type d -print | while read d; do [ -f "$d/INDEX.md" ] || echo "missing: $d/INDEX.md"; done
```
Then, for each index, confirm every listed entry exists and every entry on disk is listed.

### Regenerate (only when asked)
Rebuild all indexes from disk, keeping existing Purpose text where the entry already exists and
marking new entries `TODO purpose`. Never overwrite a written purpose with a generated one.

## Report
Indexes created / updated / removed, one path per line. Missing or stale entries found, if any.
