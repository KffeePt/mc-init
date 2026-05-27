#!/usr/bin/env python3
"""Generic image-generation helper for Hermes image-gen skill.

This script is intentionally named for the action, not a provider. It currently
supports Gemini-compatible image generation when google-genai is installed.

Usage:
  python scripts/image_generate.py --prompt prompt.txt --out image.png --aspect-ratio 1:1
  python scripts/image_generate.py --prompt prompt.txt --out image.png --image ref1.jpg --image ref2.jpg

Secrets are loaded from environment or ~/.hermes/.env and are never printed.
"""
from __future__ import annotations

import argparse
import base64
import mimetypes
import os
from pathlib import Path

DEFAULT_MODEL = "gemini-3-pro-image-preview"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def find_api_key() -> str:
    for env_path in [Path.cwd() / ".env", Path.home() / ".hermes" / ".env"]:
        load_dotenv(env_path)
    for key_name in ("IMAGE_GEN_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "NANOBANANA_API_KEY"):
        value = os.getenv(key_name)
        if value:
            return value
    raise SystemExit(
        "Missing API key. Set IMAGE_GEN_API_KEY, GEMINI_API_KEY, GOOGLE_API_KEY, or compatible provider key in environment or ~/.hermes/.env."
    )


def image_part(path: Path):
    from google.genai import types

    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return types.Part.from_bytes(data=path.read_bytes(), mime_type=mime)


def extract_image_bytes(response) -> bytes:
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                data = inline.data
                if isinstance(data, str):
                    return base64.b64decode(data)
                return bytes(data)
    for part in getattr(response, "parts", []) or []:
        inline = getattr(part, "inline_data", None)
        if inline and getattr(inline, "data", None):
            data = inline.data
            if isinstance(data, str):
                return base64.b64decode(data)
            return bytes(data)
    text = getattr(response, "text", None)
    raise SystemExit(f"No image bytes found in response. Text response: {text!r}")


def normalize_output_format(out: Path) -> None:
    if out.suffix.lower() != ".png":
        return
    try:
        from PIL import Image
    except Exception:
        return
    try:
        with Image.open(out) as im:
            if im.format == "PNG":
                return
            im.convert("RGBA").save(out, "PNG")
    except Exception as exc:
        raise SystemExit(f"Generated file exists but could not be normalized to PNG: {out} ({exc})")


def generate(prompt: str, out: Path, images: list[Path], model: str, aspect_ratio: str) -> None:
    from google import genai
    from google.genai import types

    api_key = find_api_key()
    client = genai.Client(api_key=api_key)

    full_prompt = prompt.strip() + f"\n\nOutput requirements: aspect ratio {aspect_ratio}; image only; no watermark."
    contents = [full_prompt]
    contents.extend(image_part(p) for p in images)

    config = types.GenerateContentConfig(response_modalities=["IMAGE"])

    try:
        response = client.models.generate_content(model=model, contents=contents, config=config)
    except TypeError:
        response = client.models.generate_content(model=model, contents=contents)

    data = extract_image_bytes(response)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    if out.stat().st_size == 0:
        raise SystemExit(f"Generated output is empty: {out}")
    normalize_output_format(out)
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate or edit images through the configured image backend.")
    parser.add_argument("--prompt", required=True, type=Path, help="Prompt text file")
    parser.add_argument("--out", required=True, type=Path, help="Output image path")
    parser.add_argument("--image", action="append", default=[], type=Path, help="Optional reference/input image")
    parser.add_argument("--model", default=os.getenv("IMAGE_GEN_MODEL", os.getenv("NANOBANANA_MODEL", DEFAULT_MODEL)))
    parser.add_argument("--aspect-ratio", default="1:1")
    args = parser.parse_args()

    missing = [p for p in [args.prompt, *args.image] if not p.exists()]
    if missing:
        raise SystemExit("Missing input path(s): " + ", ".join(str(p) for p in missing))
    generate(args.prompt.read_text(encoding="utf-8"), args.out, args.image, args.model, args.aspect_ratio)


if __name__ == "__main__":
    main()
