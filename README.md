# Streetview Analysis Pipeline

A local pipeline for selecting study-area coordinates, identifying side-facing street views, validating image selections, and preparing for VLM scoring and analysis.

**Data filtering, annotation, visual classification, and model evaluation are implemented and tested.** VLM scoring and downstream analysis are planned. Full-dataset processing has not yet been run.

## Task and Deliverables

Each location has four images named `longitude_latitude_angle_extra.png`, with angles of 0, 90, 180, and 270 degrees. The pipeline processes only coordinates in the study-area point list and selects two images facing the sides of the road.

The angles do not directly identify forward, backward, left, or right relative to the road. The model compares the opposing pairs 0/180 and 90/270; the annotation interface allows any two images to be selected. `side_a` and `side_b` are reference labels, not physical left/right directions.

Deliverables are a **selection manifest and an image-reading script**. Images remain in the original local ZIP archives. Subsequent VLM jobs can read image bytes from the manifest without repackaging or uploading the images.

## Results

| Stage | Sample | Method | Result |
|---|---|---|---|
| Initial experiment | 50 locations | Zero-shot CLIP with opposing-pair selection | 44/50 agreement, 88%; annotation certainty was not systematically recorded |
| Fresh-sample validation | 100 locations | Fixed zero-shot CLIP baseline | Certain: 77/84, 91.7%; uncertain: 8/16, 50% |
| Classifier experiment | The 84 certain locations above | Frozen CLIP features plus logistic regression; five-fold validation grouped by location | Out-of-fold: 81/84, 96.4%; baseline: 77/84 |
| Independent holdout | 30 new locations, excluding the previous 150 locations and identical images | Frozen classifier trained on 84 locations | Certain: 24/25, 96%; uncertain: 2/5, 40% |

Agreement requires both selected images at a location to match the human selection, ignoring a/b order. Disagreements on uncertain annotations are not automatically definitive model errors. Small-sample performance does not guarantee full-dataset accuracy.

## Repository Structure

- `scripts/`: sampling, data inspection, the annotation server, feature extraction, training, evaluation, and image reading.
- `web/`: local annotation interfaces for the 50-, 100-, and 30-location rounds; no images or annotation data.
- `docs/methodology.md`: methods, validation splits, manifest fields, and limitations.
- `docs/iteration_log.md`: the actual experiment sequence, documented retrospectively rather than reconstructed as Git history.
- `docs/roadmap.md`: plans for full-dataset processing, review, and subsequent VLM analysis.
- `results/aggregate_metrics.json`: aggregate results without individual coordinates.

The experiment scripts retain fixed sample sizes and round-specific directories for traceability. They are not yet a general-purpose batch-processing product.

## Local Setup and Execution

The tested environment is Python 3.12 on an Apple M2 Pro with 16 GB of unified memory, using PyTorch MPS. CPU execution is available on other platforms, but dependency compatibility needs to be verified.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set your private workspace and the directory containing the four original ZIPs.
export STREETVIEW_WORKSPACE="$PWD/workspace"
export STREETVIEW_ARCHIVE_DIR="$STREETVIEW_WORKSPACE/raw"
python scripts/install_annotation_assets.py
# Replace this example filename with your actual study-area XLS filename.
python scripts/inspect_data.py --centers "$STREETVIEW_WORKSPACE/raw/center_points.xls"

# Round 1: sample locations, open the interface, and complete human annotation.
python scripts/prepare_sample.py
python scripts/annotation_server.py --port 8765 --open-browser
# In another terminal with the same environment variables, after annotation:
python scripts/evaluate_clip.py

# Round 2: predict before annotation; model answers remain hidden in the interface.
python scripts/prepare_validation100.py
python scripts/predict_validation100.py
STREETVIEW_ANNOTATION_DIR="$STREETVIEW_WORKSPACE/annotation100" \
  python scripts/annotation_server.py --port 8768 --open-browser
# After annotation:
python scripts/compare_validation100.py
python scripts/train_lightweight.py

# Round 3: independent holdout validation of the trained classifier.
python scripts/prepare_validation30.py
python scripts/predict_validation30.py
STREETVIEW_ANNOTATION_DIR="$STREETVIEW_WORKSPACE/annotation30" \
  python scripts/annotation_server.py --port 8769 --open-browser
# After annotation:
python scripts/compare_validation30.py
```

The first CLIP run downloads the official model weights. Subsequent scripts use the cached model, and inference runs locally. Reproducing the reported study metrics requires the private images and annotations; they are not included in a fresh workspace.

Image-reading examples:

```bash
python scripts/read_selected.py "$STREETVIEW_WORKSPACE/annotation30/annotations.csv"
python scripts/read_selected.py "$STREETVIEW_WORKSPACE/annotation30/annotations.csv" --output "$STREETVIEW_WORKSPACE/selected_images"
```

The reader processes only the two images in records with `status=confirmed`. Records marked `needs_review` contain candidate selections and require review before use in the final analysis.

## Data Boundaries

The public repository contains only code, methods, interface templates, and aggregate metrics. Original images, the study-area point table, coordinate manifests, human annotations, per-location predictions, image features, model weights, generated reports, and local environments are excluded.

This repository grants no redistribution rights to the original data. Models and dependencies remain subject to their respective terms.
