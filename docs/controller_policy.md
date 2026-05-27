# Main-Only Init Authority

The main controller machine owns init/bootstrap skills.

Child machines may run this extracted package once, but they should not receive reusable init skills by default.

Default child-safe imports:
- `skills/core-common/plan-mode/SKILL.md`
- `skills/core-common/get-artifact/SKILL.md`
- `memories/xan_preferences.md`
- `seeds/SOUL.md`
- `seeds/sync_policy.yaml`
- `seeds/Agent Message Contract.md`

Not imported by default:
- reusable init skills
- secrets
- private keys
- raw memory dumps
- local/private skills from other machines
