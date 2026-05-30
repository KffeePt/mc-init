# 2026-05-22 — Windows `repos` Folder Classification Lessons

Context: mapping `C:\Users\santi\Documents\Source\Python\repos`, which had been moved under `Source/Python` but actually contained mixed projects.

## Durable Lessons

- A folder's current parent is weak evidence. `Source/Python/repos` contained C/C++, Go, JavaScript/TypeScript, Python, archives, empty folders, and tool residue.
- Marker priority can misclassify mixed/native projects:
  - `requirements.txt` inside or beside C/C++ tooling does **not** automatically make the project Python.
  - `.sln` files do **not** automatically imply .NET; Visual Studio C++ projects can use `.sln`, `.vcxproj`, `.filters`, CMake, and C/C++ source as dominant evidence.
- Use marker files plus extension dominance plus samples. If they disagree, mark review-required or manually correct the map.
- Case-near sibling folders on Windows (`repos` and `Repos`) must be inspected before moves. They can represent distinct folders from WSL's view but confusing/fragile paths for human Windows usage.
- For large Windows trees from WSL, Python `os.walk` over `/mnt/c` can be slow enough to time out. A PowerShell-side bounded scanner is often faster and avoids WSL filesystem overhead.
- Do not trust generated classifier output blindly. Save both raw classifier output and a refined operator map when corrections are made.

## Good Artifact Set

- `ReposClassification.json` — machine-readable raw inventory
- `ClassificationPlan.md` — raw classifier report
- `RefinedMoveMap.md` — corrected human/operator map
- `FileTree.txt` — bounded tree view

## Recommended Classification Corrections Pattern

When the automated classifier gives a bucket:

1. Check marker files.
2. Check dominant extension/file profile.
3. Check top-level samples.
4. Look for generated/build/tooling residue.
5. If marker and extension profile conflict, prefer a review bucket or a refined map entry over automatic movement.

Example correction shape:

```text
Automatic: Source/DotNet because .sln exists.
Correction: Source/C_CPP because .cpp/.h/.vcxproj/.filters/CMake dominate and .sln is Visual Studio container metadata.
```
