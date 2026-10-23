"""Compose a versioned scoring prompt with privately supplied rubric text."""

import argparse
import hashlib
import json
from pathlib import Path


def compose(version_dir: Path, stage: str, rubric_text: str) -> str:
    config = json.loads((version_dir / "config.json").read_text(encoding="utf-8"))
    entry = config["stages"][stage]
    transform = config.get("rubric_transform")
    if transform:
        if transform.get("kind") != "before_heading":
            raise ValueError("Unsupported rubric transformation.")
        heading = transform["heading"]
        if rubric_text.count(heading) != 1:
            raise ValueError("Expected the full organized rubric with exactly one cutoff heading.")
        rubric_text = rubric_text[:rubric_text.index(heading)]
    return (
        (version_dir / entry["prefix"]).read_text(encoding="utf-8")
        + rubric_text
        + (version_dir / entry["suffix"]).read_text(encoding="utf-8")
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=["v0", "v1_compact", "v2_organized", "v3_evidence_aligned", "v4_spatial", "v5_safety_only", "v6_target_evidence"], required=True)
    parser.add_argument("--stage", choices=["overall", "side_A", "side_B"], required=True)
    parser.add_argument("--rubric-text", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-pilot-hash", action="store_true")
    args = parser.parse_args()
    version_dir = Path(__file__).resolve().parents[1] / "prompts" / "qwen_scoring" / args.version
    # Preserve extracted rubric line endings and characters for exact hash checks.
    rubric = args.rubric_text.read_bytes().decode("utf-8")
    try:
        prompt = compose(version_dir, args.stage, rubric)
    except ValueError as exc:
        parser.error(str(exc))
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    config = json.loads((version_dir / "config.json").read_text(encoding="utf-8"))
    if args.verify_pilot_hash:
        expected = config.get("pilot_composed_prompt_sha256", {}).get(args.stage)
        if expected is None:
            parser.error("This version has no archived pilot hash; no output written.")
        if digest != expected:
            parser.error("Composed prompt differs from the archived pilot hash; no output written.")
    if args.output.exists():
        parser.error("Output already exists; choose a new filename.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="") as stream:
        stream.write(prompt)
    print(json.dumps({"version": args.version, "stage": args.stage, "sha256": digest}))


if __name__ == "__main__":
    main()
