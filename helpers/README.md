# Hermes Helpers

Reusable copied scripts are called **helpers**.

Canonical Windows root:

```text
C:\Users\santi\Documents\Hermes\helpers\
```

Canonical WSL root:

```text
/mnt/c/Users/santi/Documents/Hermes/helpers/
```

Organization rule:

```text
helpers/<skill-name-or-domain>/<helper-file>
```

A skill may still bundle scripts inside its own `scripts/` or `templates/` directory for portability, but any script meant for user/agent execution or copying should also be explicitly staged here.

Current helper groups:

- `init/` — initializer helper entrypoint.
- `screenshot/` — Windows screenshot capture helper.
- `get-movie/` — Plex/movie helper scripts.
- `get-show/` — qBittorrent/Plex/show flatten/refresh helpers.
- `media/` — shared qBittorrent smart organization hooks.
- `storage-explorer/` — hash verification/comparison helpers.
