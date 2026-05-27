# Visual Reference Search and Iterative Likeness Correction

## Trigger
Use when Xan asks for likeness accuracy or says things like:

- "grab references"
- "make it look more like this"
- "use this as reference"
- "the beard/hat/face/color is wrong"
- "show references first"

## Reference-first workflow

1. Search candidate visual references unless Xan already supplied images.
2. Save candidates and source metadata in the task artifact folder.
3. Build a labeled contact sheet.
4. Show the sheet and give a short read on strongest/weakest options.
5. Wait for Xan to pick references before generation unless he explicitly says to choose automatically.
6. Use 2-4 reference images max for likeness; too many inputs average identity into mush.

## Candidate scoring

Prefer:

- correct actor/character/version/adaptation
- clear face and costume cues
- matching angle/mood for the requested output
- high resolution with minimal watermark/UI clutter
- one primary close likeness reference plus one supporting full-costume/context reference

Reject or de-prioritize:

- wrong adaptation or actor
- promotional shots with the wrong costume/version
- low-res crops where the face is not visible
- screenshots dominated by phone UI, watermarks, or unrelated characters, unless Xan chooses them specifically

## Iterative correction rules

When Xan supplies a new reference after a generated image:

1. Treat the new image as the strongest correction reference for the specific complaint.
2. Preserve prior explicit constraints unless Xan overrides them.
3. Name corrected attributes plainly in the prompt: beard thickness, hat shape, face angle, eyepatch color, background color, coat color.
4. If a color is requested for the background, separate it from object colors.
5. Run visual QA against each correction before reporting success.

## Prompt pattern for likeness corrections

```text
Goal: Revise/generate <subject> so it looks more like the supplied reference.
Primary correction: <what Xan corrected>.
Reference likeness: match <face angle, expression, beard, hat, costume cues>.
Preserve constraints: <coat color, eyepatch placement, aspect ratio, style>.
Background/style: <specific requested background color/panes/motifs>.
Negative constraints: no wrong costume, no phone UI, no watermark.
Output: square PNG, image only.
```
