# First-time setup

This is a YOLO-style ONNX detection service template, with a documented path
for other detectors and tasks. A YOLOv8 ONNX export needs only `config.yaml`.
Other detectors follow "Other detectors: RF-DETR" below, a tested worked
example. Other tasks follow
"Adding a new task".

Models are not committed to git, so a fresh checkout has no model file. The
app still runs, but `/ping` and `/predict` return 503 and `/health` lists what
is missing in `setup_errors`. Complete this checklist first.

## Checklist
1. Edit `config.yaml`: `model.path` (must be under `models/`), `model.url`
   (a direct link to the `.onnx` file), `model.labels`, `model.input_size`,
   `model.channel_order`, `model.normalize`.
2. Locally, download the file to `model.path`, for example
   `curl -fL -o models/yolov8n.onnx <model.url>`. In CI, the workflow
   downloads `model.url` with `wget` for you.
3. If your detector's output layout differs from YOLOv8 (cx, cy, w, h plus
   class scores, shape (1, 4+classes, N)), edit
   app/pipeline/detection/postprocess.py. If its input handling differs
   (resize, color order, scaling), edit preprocess.py.
   Check /health `model_io` to see your model's real input and output shapes.

## Design rule
When a design choice is open, follow the most common convention in the field.

## Adding a new task (NLP, tabular, other)
1. Create app/pipeline/<task>/ with a Pipeline subclass (see app/pipeline/base.py).
2. Register it in app/pipeline/__init__.py.
3. Add the task name to the `task` Literal in app/config.py.
4. Set `model.task` in config.yaml.
5. Add unit tests that feed fake arrays and check the output.
6. If the result shape differs from detections, add response models in
   `app/schemas/` and a router in `app/routers/`.
The runtime in app/services/onnx_runtime.py is task-agnostic. A new task or
model never needs to edit it. Runtime-wide changes that help every model
(execution providers, GPU fallback, session options) are fine.

## Other detectors: RF-DETR
RF-DETR (Roboflow) is the worked example of a detector whose layout differs
from YOLOv8. It runs in
[rfdetr-model-deployment](https://github.com/seemab-yamin/rfdetr-model-deployment)
with the Nano ONNX export from
`https://huggingface.co/PierreMarieCurie/rf-detr-onnx/resolve/main/rf-detr-nano.onnx`.
The same steps apply to YOLOv5 (objectness column), SSD, and exports with NMS
built in.

1. Run the app with the model and read `/health` `model_io`. Do not code
   from assumptions. For RF-DETR Nano it shows input `input`
   `[1, 3, 384, 384]` and outputs `pred_boxes` `[1, 300, 4]` and
   `pred_logits` `[1, 300, 91]`. The Base export uses a 560x560 input.
2. `config.yaml`: set `model.path`, `model.url`, `input_size`, and
   `model.labels`. The label count must match the class dimension. RF-DETR's
   91 logits are indexed by COCO category id, so the list starts with
   `__background__` and has `N/A` for unused ids. The pipeline reports a
   mismatch in `setup_errors`. Set `confidence_threshold: 0.5`, the RF-DETR
   default.
3. `preprocess.py`: plain resize to the input size (no letterbox), RGB,
   divide by 255, then ImageNet mean `[0.485, 0.456, 0.406]` and std
   `[0.229, 0.224, 0.225]`, NCHW. Set mean and std with the `model.mean`
   and `model.std` keys in `config.yaml`. Only the resize needs code: replace
   the letterbox with a plain resize, and return a context that maps boxes
   back to original-image pixels.
4. `postprocess.py`: `pred_boxes` are normalized cx, cy, w, h. Apply a
   sigmoid to `pred_logits`, take the best class per query, keep scores above
   `confidence_threshold`, convert to `[x1, y1, x2, y2]` in original pixels,
   and skip NMS (drop `iou_threshold` from the config). Return the same dicts
   as the reference: `class_id`, `class`, `confidence`, `bbox`.
5. `app/pipeline/detection/__init__.py`: the reference passes only
   `outputs[0]` to postprocess. Pass every output.
6. Replace the YOLOv8 fake-array tests in
   `tests/unit/test_detection_pipeline.py` with fakes shaped like your
   model's outputs. `/predict` tests stay unchanged, because the response
   shape does not change.
7. Check the boxes on a real image with `optional/annotate/`, then push and
   confirm CI is green.

## Config fields
See comments in `config.yaml`. Unknown keys are rejected on purpose.
- `model.url` (optional, direct link): CI downloads the model from here to
  `model.path`. The app itself never downloads it.
- `model.sha256` (optional, 64 hex chars): CI fails the download if the
  file's SHA-256 differs. Update it whenever you change `model.url`. Get it
  with `shasum -a 256 models/<file>.onnx`.
- `model.mean`, `model.std` (optional, 3 numbers each): per-channel
  normalization applied after `normalize`. Leave unset for YOLOv8.
- `inference.providers`: tried in order. Providers this ONNX Runtime build
  lacks are skipped with a warning, and CPU is always the fallback.
  `/health` `model_io` shows the active and requested providers.
- `inference.max_upload_mb` (int, default 10): `/predict` rejects larger uploads with 413.

## Calling /predict
```bash
curl -F "file=@path/to/image.jpg" localhost:8000/predict
```
Send one JPEG, PNG, or WebP image in the form field `file`. Until setup is
complete, `/predict` returns 503 with the same `setup_errors` as `/health`.
Fix those first. A 500 with a specific message (for example a labels count
mismatch) means `config.yaml` or `app/pipeline/` needs a change. See the
README for the full error table.

## Mocks in unit tests
Unit tests never need a real model.
- `tests/unit/test_onnx_runtime.py` fakes ONNX input metadata and sessions.
- `tests/unit/test_startup.py` patches `app.main.load_model` with a fake model.

If you change the loader (for example to support multiple inputs), update
these tests and the fakes to match. If you change the pipeline in
`app/pipeline/`, add tests that feed fake arrays and check the output.
Do not add a real .onnx file to the repo to make tests pass.

## CI behavior with no model
The workflow in `.github/workflows/ci.yml` reads `model.url` and
`model.path` from `config.yaml` and downloads the model with `wget` before
building the image. Registry settings go under Settings > Secrets and
variables > Actions:

| Name | Kind | Purpose |
|---|---|---|
| `DOCKERHUB_USERNAME` | secret | Registry username |
| `DOCKERHUB_TOKEN` | secret | Registry access token |
| `MODEL_URL` | repository variable (optional) | Overrides `model.url` without a commit |
| `MODEL_SHA256` | repository variable (optional) | Checksum for the `MODEL_URL` file. Ignored with a warning when the URL comes from `config.yaml` |

What runs:
1. No `model.url`: unit tests only. Every other step is skipped and the run is green.
2. `model.url` set: CI downloads the model to `model.path` (it must be under
   `models/`), builds the image, starts it, waits for `/ping`, and runs
   `tests/integration`. Push is skipped without the registry secrets.
3. `model.url` and both secrets set, push to `main`: everything above, then
   the image is pushed with the commit SHA tag and `latest`. Pull requests
   never push.

`model.url` must be a direct file link, such as a GitHub release asset or a
Hugging Face `resolve/main/...` URL. A web page link downloads HTML, and the
download step fails with a message naming where the URL came from. With
`model.sha256` set, a file that differs from the pinned one fails with the
expected and actual hashes. A file
that downloads but is not a valid model fails at the `/ping` wait, and the
log prints `/health` with `setup_errors` that say what is wrong.

Reading the job summary: open the run, then the summary at the top of the
page. It shows a table with each stage's result and one line for each skipped
stage that names exactly what to configure, plus the model path and where
its URL came from. After a push it shows the pushed
image reference. Deploy the SHA tag, not `latest`.

The integration tests only check the endpoints and response shape, not
specific detections, because the template cannot know what your model finds.