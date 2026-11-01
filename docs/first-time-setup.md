# First-time setup

The template starts with no model. It runs, but `/ping` returns 503 and
`/health` lists what is missing. Complete this checklist first.

## Checklist
1. Put your `.onnx` file in `models/`.
2. Edit `config.yaml`: `model.path`, `model.labels`, `model.input_size`,
   `model.channel_order`, `model.normalize`.
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
The runtime in app/services/onnx_runtime.py is task-agnostic. Do not edit it for a new task.

## Detection layouts not covered by the reference
YOLOv5 (has an objectness column), SSD, DETR and exports with NMS built in.
Edit postprocess.py for these.

## Config fields
See comments in `config.yaml`. Unknown keys are rejected on purpose.
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
(added in point 5)