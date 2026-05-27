# 2026-05-23 Documents Remaining Work And Naming

## Trigger

Xan asked to finish the unresolved Documents organization work and corrected two workflow/style issues:

- user-facing folder names should use spaces, not underscores;
- `Remaining work:` must carry unresolved items forward across turns unless they are actually fixed.

## Durable Lessons

### Remaining-work continuity

When a prior response lists unresolved work, a later response must not say `Remaining work: none` just because the current tiny task was completed. Carry prior unresolved items forward until they are remediated, cancelled, or explicitly deferred.

### Naming convention

For Xan's personal Documents organization, prefer readable space-separated folder names:

- good: `School And Work`, `Duplicate Candidates`, `Credentials And Keys`
- avoid: `School_And_Work`, `Duplicate_Candidates`, `Credentials_And_Keys`

Exception: do not rename paths where underscores are part of tool/project semantics, package names, dataset conventions, or generated assets unless Xan explicitly approves path breakage.

### Safe rename scope

Safe default scope for underscore-to-space rename passes:

- top-level personal containers;
- known review/archive/media containers already created for organization;
- small policy folders such as `Important` and `School And Work`.

Avoid recursive rename passes inside:

- `Source`;
- `GitHub`;
- repositories and nested project internals;
- datasets;
- venvs and package/vendor folders;
- `.git` and generated build/cache folders;
- Obsidian vault internals unless using Obsidian-aware migration.

Always write a rename manifest and verify only the approved scope afterward.

### Bounded GitHub scan pattern

For Windows Documents `GitHub`, use a bounded Windows-native scan rather than slow WSL traversal. Exclude or cap dependency/cache/build/model folders. Report large children and explicitly label capped lower-bound folders.

### Takeshi cleanup pattern

Treat Takeshi datasets as protected. For dedup:

1. group candidates by same name and size;
2. hash with SHA-256;
3. report exact duplicate extra copies and reclaimable bytes;
4. require explicit approval before deleting or replacing with shared layout.

For venv cleanup:

1. inspect dependency manifests first;
2. size primary venvs separately from dataset folders;
3. mark venvs rebuildable candidates, not automatic deletes.

## Output Pattern

Final report should include:

- naming changes and verification;
- bounded GitHub total and top children;
- exact duplicate Takeshi groups and potential recoverable space;
- venv total and manifest count;
- policy decision for `Important`, `Obsidian Vault`, and `School And Work`;
- `Remaining work:` carrying only optional approval-gated destructive actions.
