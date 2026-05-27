# Repos Review Cleanup and Space-Mapping Lessons

Session signal: after moving ready repo projects, Xan asked to inspect/classify remaining review items, move them, scan for out-of-place folders, then perform Filelight-style space mapping.

## Durable lessons

- After a ready-only move pass, treat remaining review items as a second manifest-driven pass, not as loose manual moves.
- For review leftovers, create explicit destinations such as:
  - `To_Review/Duplicate_Candidates`
  - `To_Review/Archive_Files`
  - `To_Review/Empty_Or_Test_Folders`
  - `To_Review/Tool_Residue`
  - language-specific `Source/<Language>` buckets for clear projects
- Move an emptied container folder to review only after verifying it is empty; do not delete it silently.
- Scan for more out-of-place folders after cleanup, but distinguish semantic-policy folders from storage problems. Example: `Important`, `Obsidian Vault`, and `School_And_Work` may need organization policy, not disk cleanup.
- Pair tree inspection with space inspection: hierarchy tells what something is; Filelight-style accounting tells whether it matters operationally.
- For all cleanup responses, include `Remaining work:` in text and audio when unresolved review items, timed-out scans, or policy decisions remain.

## Safe execution shape

```text
1. Inspect review items with metadata/tree/size.
2. Generate manifest and restore script.
3. Move only clearly classified items; no deletes.
4. Verify each moved destination exists and original source is gone.
5. Verify protected/excluded paths were not touched.
6. Save summary under Hermes/Artifacts.
7. Report remaining work explicitly.
```
