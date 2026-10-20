"""Calculate aggregate-only VLM usage costs from private pilot response records.

Input is the local predictions.json array. Images, coordinates, evidence, and
reference scores are never copied into the output. No network calls are made.
"""

import argparse
import json
from pathlib import Path

PRICES = {
    "qwen3-vl-plus": {"input": 1.0, "cached_input": 0.2, "output": 10.0},
    "qwen3.8-flash": {"input": 0.8, "cached_input": 0.1, "output": 2.7},
    "qwen3.7-plus": {"input": 2.0, "cached_input": 0.4, "output": 8.0},
    "qwen3.8-max": {"input": 12.0, "cached_input": 1.5, "output": 36.0},
}


def summarize(records):
    totals = {}
    missing_usage = 0
    for record in records:
        model = record["model_requested"]
        if model not in PRICES:
            raise ValueError(f"No archived price for model: {model}")
        usage = record.get("response", {}).get("usage")
        if usage is None:
            missing_usage += 1
            continue
        row = totals.setdefault(model, dict(
            metered_responses=0, input_tokens=0, cached_input_tokens=0,
            output_tokens=0, successful_responses=0,
        ))
        incoming = usage["prompt_tokens"]
        cached = usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
        outgoing = usage["completion_tokens"]
        if not (0 <= cached <= incoming and outgoing >= 0):
            raise ValueError("Invalid API usage counts")
        row["metered_responses"] += 1
        row["successful_responses"] += str(record.get("http_status")) == "200"
        row["input_tokens"] += incoming
        row["cached_input_tokens"] += cached
        row["output_tokens"] += outgoing
    for model, row in totals.items():
        price = PRICES[model]
        row["cost_CNY"] = (
            (row["input_tokens"] - row["cached_input_tokens"]) * price["input"]
            + row["cached_input_tokens"] * price["cached_input"]
            + row["output_tokens"] * price["output"]
        ) / 1_000_000
        row["no_cache_cost_CNY"] = (
            row["input_tokens"] * price["input"]
            + row["output_tokens"] * price["output"]
        ) / 1_000_000
    return {
        "pricing_date": "2026-10-20", "region": "cn-beijing", "currency": "CNY",
        "models": totals, "records_without_usage": missing_usage,
        "note": "Usage-based estimate, not account billing. Missing usage does not establish zero charge.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new filename.")
    records = json.loads(args.predictions.read_text(encoding="utf-8"))
    result = summarize(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print("Saved aggregate usage report.")


if __name__ == "__main__":
    main()
