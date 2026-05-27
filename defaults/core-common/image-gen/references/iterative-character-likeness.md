# Iterative Character Likeness Revision Notes

## Trigger
Use this reference when Xan asks for a generated character image to be refined after seeing the result, especially corrections like:

- “beard is too thin”
- “also the hat”
- “make it look more like this reference”
- “keep X but change Y”

## Workflow

1. Treat the user-supplied corrected image as the strongest reference for the specific corrected attribute.
2. Keep earlier selected likeness references if they still anchor identity, but avoid overloading the model. Usually 2–3 references is enough.
3. Preserve explicit previous constraints in the new prompt. Do not let a new reference image silently override them.
4. Convert vague corrections into concrete visual constraints.
5. Include negative constraints for the failure modes observed in the previous output.
6. QA the generated image against each user correction before delivering.

## Prompt pattern for corrections

```text
Primary correction from user: <correction>. Make this concrete: <visual dimensions, color, placement, density, shape>.

Preserve from previous instructions: <constraints that must remain true>.

Do not copy conflicting traits from the new reference: <e.g. wrong clothing color, phone UI, watermark>.

Negative constraints: avoid <specific previous failure modes>.
```

## QA checklist

- [ ] Did the corrected attribute visibly change?
- [ ] Did earlier constraints survive?
- [ ] Did the new reference accidentally introduce unwanted traits?
- [ ] Is the output still in the requested style/composition?
- [ ] Is the final file actually the requested format, not just named that way?
