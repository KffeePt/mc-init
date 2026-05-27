# 2026-05-22 Documents Execution + Media Cleanup Notes

Session-specific details from Xan's Documents cleanup after the dry-run plan.

## Durable workflow lessons

- Exclusions must be interpreted broadly. Xan said to leave `GitHub` alone; an execution pass moved `03_Code_And_AI/GitHub` because it only excluded top-level `GitHub/`. The move was restored immediately. Future runs should protect both top-level and nested same-name buckets unless the user narrows the scope.
- After moving projects, explicitly verify protected/excluded paths still exist where expected.
- Avoid planning parent and child moves in one pass. Moving `ComfyUI` made later child candidates such as `ComfyUI/input` show as `source_missing`. That is harmless but noisy and can obscure real problems.
- For project organization, move standalone project/application roots as units unless the parent is clearly only a container.

## Media cleanup pattern

- Zero-byte screenshot/image files can be treated as junk candidates after user approval. Delete them only after approval and log exact paths. Restore scripts cannot meaningfully restore zero-byte content.
- Saved webpage debris in `My Pictures` should be moved as coherent pairs:
  - `<saved page>.htm` / `.html`
  - matching asset folder like `<saved page> Archivos`, `<saved page>_files`, or `<saved page> Files`
- Do not delete individual saved-webpage assets by hash; the HTML file may reference them. Move the whole debris set to review, or delete the whole saved page set only after approval.
- Windows `desktop.ini` should be left alone and logged as metadata.
- Non-media data files in picture/music/video folders, e.g. `.npy`, belong in `99_To_Review/Data_Artifacts/`.

## Artifacts from the session

- Dry-run inspection: `Documents/Hermes/Artifacts/2026-05-22/21-50-34/DocumentsDryRunInspection/`
- Approved execution: `Documents/Hermes/Artifacts/2026-05-22/22-12-08/DocumentsExecuteApprovedMoves/`
- Media cleanup: `Documents/Hermes/Artifacts/2026-05-22/22-22-43/MediaFoldersOrganization/`

These paths are examples, not hardcoded future targets.
