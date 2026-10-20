"""Reproduce v2 rubric grouping from the two authorized private PDF text extracts.

This is a document-specific repair, not a general PDF parser. Verify the source
PDF layout before applying it to a different rubric or extraction method.
"""

import argparse
from collections import Counter
from pathlib import Path
import re
import unicodedata

DIMS = ["通行安全", "沿街界面", "绿荫停留", "环境维护"]
KEYS = ["pedestrian_safety", "street_interface", "greenery_staying", "environmental_maintenance"]


def split_once(text, token):
    if text.count(token) != 1:
        raise ValueError(f"Unexpected extraction structure at marker: {token}")
    return text.split(token, 1)


def organize_rubric(raw, scope):
    if scope not in ("overall", "single_side"):
        raise ValueError("Scope must be overall or single_side")
    normalized = unicodedata.normalize("NFKC", raw).translate(
        str.maketrans("⻅⻆⻋⻓⻔⻚⻛⻢⻬", "见角车长门页风马齐")
    )
    text = re.sub(r"\s+", "", normalized).replace("分值具体判定标准", "")
    main, tail = split_once(text, "2.分维度评分标准")
    starts = [tail.index(f"2.{i+1}" + dim) for i, dim in enumerate(DIMS)]
    definitions, bands, limits = [], [], []
    for i in range(4):
        segment = tail[starts[i]:starts[i+1] if i < 3 else None]
        _, rest = split_once(segment, "一级定义")
        definition, rest = split_once(rest, "分值规则")
        band, limit = split_once(rest, "硬性限制")
        definitions.append(definition)
        bands.append(band)
        limits.append(limit)
    source_characters = Counter("".join([main, *definitions, *bands, *limits]))
    if scope == "overall":
        if limits[0] or limits[2]:
            raise ValueError("Unexpected overall restriction layout")
        safety, glass = split_once(limits[1], "玻璃墙只有可视联系")
        street, green = split_once(definitions[3], "可见绿化面积不等于针对行人的遮蔽")
        green, maintenance = split_once(
            "可见绿化面积不等于针对行人的遮蔽" + green, "整体场景中双侧临街建筑"
        )
        definitions[3] = "整体场景中双侧临街建筑" + maintenance
        limits = [safety, "玻璃墙只有可视联系" + glass + street, green, limits[3]]
        title = "上海街道【整体场景】图片人工评分标准"
    else:
        if limits[0]:
            raise ValueError("Unexpected single-side restriction layout")
        street, green = split_once(limits[2], "“绿化多”不能直接替代")
        limits = [limits[1], street, "“绿化多”不能直接替代" + green, limits[3]]
        title = "上海街道【单侧】图片人工评分标准"
    if source_characters != Counter("".join([main, *definitions, *bands, *limits])):
        raise ValueError("Source rule characters were lost or added")
    output = [f"# {title}\n", "## 1. 通用原则\n", main + "\n"]
    ranges = ["0.0–0.2", "0.4–0.6", "0.8–1.0"]
    for i, (dim, key, definition, band, limit) in enumerate(zip(DIMS, KEYS, definitions, bands, limits)):
        output += [f"## 2.{i+1} {dim} ({key})\n", "### 一级定义\n", definition + "\n", "### 分值规则\n"]
        for j, (label, range_) in enumerate(zip(["低档", "中档", "高档"], ranges)):
            start = band.index(range_) + len(range_)
            end = band.index(ranges[j+1]) if j < 2 else len(band)
            paragraph = re.sub(r"(?<!\d)(0\.[01245689]|1\.0):", r"\n\1: ", band[start:end])
            output += [f"【{label} {range_}】\n", paragraph + "\n"]
        output += ["### 硬性限制\n", limit.replace("。", "。\n") + "\n"]
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overall-text", type=Path, required=True)
    parser.add_argument("--single-side-text", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    # Prepare both in memory before creating output; never replace an old version.
    results = {scope: organize_rubric(path.read_bytes().decode("utf-8"), scope)
               for scope, path in [("overall", args.overall_text), ("single_side", args.single_side_text)]}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for scope, text in results.items():
        with (args.output_dir / f"{scope}.txt").open("x", encoding="utf-8", newline="") as stream:
            stream.write(text)
    print("Saved two organized private rubrics in the new directory.")


if __name__ == "__main__":
    main()
