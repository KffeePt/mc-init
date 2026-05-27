---
name: image-gen
description: Use when Xan asks to generate, edit, transform, or visually redesign images, posters, thumbnails, concept art, visual explainers, or presentation-style infographics using the best available image-generation backend.
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [image-generation, image-editing, visual-design, infographics, artifacts]
    related_skills: [baoyu-infographic, baoyu-article-illustrator, popular-web-designs, sketch, task-artifacts-delivery]
---

# Image Generation

## Overview

Use this skill for general image generation and image editing. The skill is named for the action it performs: `image-gen`. Do not name a general-purpose skill after one model, provider, product, or codename unless the skill truly only operates that specific thing.

This skill covers:

- Text-to-image generation.
- Editing an existing image with instructions.
- Creating thumbnails, posters, concept art, UI mockups, visual explainers, and presentation-style infographics.
- Building visual variants from supplied references.
- Choosing between the built-in Hermes `image_generate` tool and a script/API backend when the task needs more control.

## When to Use

Use when the request includes:

- generate an image, picture, poster, thumbnail, wallpaper, visual, concept art, or scene;
- edit, transform, restyle, clean up, or redesign an existing image;
- create a visual explainer or presentation-style infographic;
- make visual variants from one or more references;
- use an image model/provider explicitly named by Xan.

Do **not** use image-generation models for factual charts by default. If the output contains arithmetic, exact values, or analytical relationships, render the chart programmatically first with Python/SVG/HTML. Use image generation only for requested presentation styling after the numbers are already correct.

## Naming Rule

Skill names should describe the overall action or workflow:

- Good: `image-gen`, `storage-explorer`, `media-transcoding`, `github-pr-workflow`.
- Bad for general workflows: provider/model/codename names that only describe one backend.
- Exception: provider-specific names are valid only when the workflow is genuinely locked to that provider or API.

If a provider-specific implementation becomes the default backend for a general workflow, keep the skill name general and document the backend inside the skill body or helper script.

## Backend Selection

Prefer this order:

1. **Built-in Hermes image tool** when Xan asks for ordinary generation and does not require a specific model/backend.
2. **Task-local or skill helper script** when the request needs reference images, exact file placement, retry handling, backend-specific controls, or reproducibility.
3. **Explicit provider path** only when Xan names a backend/model or the built-in tool cannot satisfy the request.

Never print API keys. Load keys from environment or Hermes-managed secret stores. If the requested backend fails, report the status/error without exposing secrets.

## Prompting Rules

Use this prompt spine:

```text
Goal: <what to make>
Subject/content: <objects, people, scene, chart data, labels>
Style: <medium, visual style, palette, brand constraints>
Composition: <layout, framing, aspect ratio, hierarchy>
Text requirements: <exact title/labels; avoid tiny unreadable text>
Constraints: <what must remain unchanged; no extra logos/text unless requested>
Output: <transparent background / PNG / poster / infographic / etc.>
```

For image edits:

- Attach or reference the source image path/URL.
- State what must be preserved.
- State what should change.
- Keep original files untouched; write edited outputs to a new artifact path.

For character/person/object likeness:

1. Search for reference images unless Xan already supplied them.
2. Save reference metadata in the task artifact folder.
3. Build a small contact sheet when several choices exist.
4. Ask Xan which references to use unless he explicitly says to choose automatically.
5. Use a small number of strong references. Too many references average the subject into soup. Soup is not identity.

## Artifact Rules

Save generated images under the shared Hermes artifact workspace:

```text
C:\Users\santi\Documents\Hermes\Artifacts\YYYY-MM-DD\HH-MM-SS\<Pascal Case Purpose>\
```

WSL equivalent:

```text
/mnt/c/Users/santi/Documents/Hermes/Artifacts/YYYY-MM-DD/HH-MM-SS/<Pascal Case Purpose>/
```

Deliver user-visible images with:

```text
MEDIA:/absolute/path/to/image.png
```

For multi-file image tasks, include a manifest listing prompt, source references, outputs, backend used, verification, and caveats. Do not include secrets.

## Helper Script

This skill may include `scripts/image_generate.py` as an optional backend helper. Use it only when the built-in image tool is insufficient or a provider-specific API path is required.

Expected generic shape:

```bash
python ~/.hermes/skills/creative/image-gen/scripts/image_generate.py \
  --prompt /path/to/prompt.txt \
  --out /path/to/output.png \
  --aspect-ratio 1:1 \
  --image /optional/reference.jpg
```

Backend/model names are implementation details. Prefer environment variables for backend-specific selection. Do not bake provider branding into the skill name.

## Quality Checks

- Verify output path exists and file size is nonzero.
- Open/analyze the image when quality or content accuracy matters.
- For factual labels/text, inspect the rendered pixels or use OCR if available.
- For charts, verify numbers outside the image model.
- Preserve originals for edits.
- Keep prompts and manifests auditable without exposing keys.

## Common Pitfalls

1. **Provider-name skill sprawl.** If the workflow is general image generation, the skill is `image-gen`; backend details live inside the skill.
2. **Using image models as calculators.** They hallucinate numbers with confidence. Render factual charts programmatically.
3. **Weak edit prompts.** “Make it better” is not an instruction. Specify what changes and what must remain fixed.
4. **Too many references.** The model blends them. Use a few strong references.
5. **No verification.** A nonzero file is not the same as a correct image. Inspect important outputs.

## Verification Checklist

- [ ] Correct workflow selected: generate, edit, variant, or visual explainer.
- [ ] Backend selected intentionally; provider/model name kept out of the skill name.
- [ ] Prompt includes goal, content, style, composition, constraints, and output format.
- [ ] Source images/references saved or cited when used.
- [ ] Output saved under the Hermes artifact workspace.
- [ ] File exists and is nonzero.
- [ ] Important outputs visually inspected.
- [ ] Delivered via `MEDIA:` when appropriate.
