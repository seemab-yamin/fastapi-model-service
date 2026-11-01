# fastapi-model-service

A template for serving an ML model as a REST API. It includes a FastAPI server, Docker image, GitHub Actions CI, tests, and an AI skill that guides code generation.

The template ships with a stock YOLOv8s object detector so it works with zero edits. Swap in any other model by changing a few files.

## What you get

- FastAPI server that loads the model once at startup
- `/predict` endpoint with input validation and a typed response
- `/health` (info) and `/ping` (readiness) endpoints
- Dockerfile with model weights baked in at build time
- GitHub Actions: unit tests, build, integration tests against the live container, push
- Images tagged with the commit SHA and `latest`
- Unit tests and integration tests (integration tests skip unless `BASE_URL` is set)
- A `SKILL.md` that tells an AI coding assistant how to adapt the template safely

## Quick start

1. Click **Use this template** on GitHub and name your new repo.
2. Clone it and install dependencies (`requirements-dev.txt` adds the test tools):

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

3. Run the server:

```bash
uvicorn app.main:app --reload
```

4. Open `http://localhost:8000/docs` and try `/predict` with an image.
5. Run the tests:

```bash
pytest tests/unit -v
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness and info. Returns 200 when the process is up, with `status`, `model_loaded`, and the model name. |
| GET | `/ping` | Readiness. Returns 503 until the model is loaded, then 200. Point platform health checks here. |
| POST | `/predict` | Runs the model on an uploaded image (`multipart/form-data`, field `file`) and returns JSON. |

### `/predict`

```bash
curl -X POST "http://localhost:8000/predict" \
  -F "file=@/path/to/image.jpg"
```

Response:

```json
{
  "filename": "bus.jpg",
  "image": {"width": 810, "height": 1080},
  "count": 1,
  "detections": [
    {"class_id": 5, "class": "bus", "confidence": 0.84, "bbox": [30.9, 231.2, 800.7, 777.7]}
  ],
  "inference_ms": 24.2
}
```

`bbox` is `[x1, y1, x2, y2]` in original-image pixels. No detections returns `count: 0` and an empty list with status 200. `inference_ms` covers the model pipeline only.

| Status | Cause |
|---|---|
| 400 | Empty file, corrupt or truncated image, or a side under 16 px |
| 413 | File larger than `inference.max_upload_mb` (default 10) |
| 415 | Content type or real file format is not `image/jpeg`, `image/png`, or `image/webp` |
| 422 | No `file` field in the form |
| 500 | Pipeline error (message says what to fix, for example a labels count mismatch) or an internal error (generic message, traceback in the server log) |
| 503 | Model not loaded. The body has `setup_errors` listing what to fix |

## Project structure

```
app/
  main.py          # lifespan, app.state, router registration
  config.py        # model name, path, limits
  routers/         # thin HTTP layer (health.py, predict.py)
  services/        # model loading and inference logic
  schemas/         # request and response models
  utils/           # shared helpers
tests/
  unit/            # run on every push
  integration/     # run against a live container
Dockerfile
requirements.txt
.github/workflows/deploy.yml
.claude/skills/fastapi-model-service/
  SKILL.md
  references/
```

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `PORT` | `8000` | Port the server listens on |
| `MODEL_NAME` | `yolov8s.pt` | Model file or identifier to load |

Secrets (API keys, registry tokens) come from env vars or CI secrets. Never commit them and never bake them into the image.

## Swap in a different model

Change only these files:

- `app/services/inference_service.py`: load and run the model
- `app/schemas/`: request and response shapes
- `app/config.py`: model name and path
- `requirements.txt`: pinned, minimal dependencies
- `Dockerfile`: the weight download line only
- `tests/`: update tests and assets to match the new output

Do not change the lifespan loading, the `app.state` pattern, the readiness logic, or the workflow job order unless you have a clear reason.

## Use the AI skill

The skill lives in `.claude/skills/fastapi-model-service/`. Open the repo root in Claude Code and it loads automatically when your request matches its description.

Example prompts:

- "Adapt this template to serve a ViT image classifier. Return the top 5 labels with scores."
- "Add an `/annotate` endpoint that draws boxes on the image."
- "The container keeps restarting after deploy. Help me debug it."

After the AI finishes, review the diff. It should touch only the swap points. If it edits the lifespan code or the workflow, reject the change and tighten the wording in `SKILL.md`.

When you hit a new class of failure, add a general pattern to `references/failure-patterns.md`.

## CI/CD

The workflow (`.github/workflows/ci.yml`) runs on every push to `main` and on every pull request:

1. Installs dependencies and runs unit tests (always)
2. Downloads the model from `MODEL_URL` to `model.path` in `config.yaml`, and builds the Docker image
3. Starts the container, waits for `/ping`, and runs integration tests against it
4. Pushes the image to Docker Hub, tagged with the commit SHA and `latest` (push to `main` only, never on pull requests)

Configure it under **Settings > Secrets and variables > Actions**:

| Name | Kind | Value |
|---|---|---|
| `MODEL_URL` | repository variable | Direct download link to the `.onnx` file (a GitHub release asset or a Hugging Face `resolve/main/...` URL, not a web page) |
| `DOCKERHUB_USERNAME` | secret | Your registry username |
| `DOCKERHUB_TOKEN` | secret | A registry access token |

| Configured | What runs |
|---|---|
| Nothing | Unit tests only. The run is green and the job summary says what to set. |
| `MODEL_URL` | Unit tests, download, build, integration tests. Push is skipped. |
| All three, push to `main` | Everything, and the image is pushed as `<username>/<repo>:<sha>` and `:latest`. |

Models are never committed to git. The job summary lists each stage's result and why any stage was skipped.

CI stops once the image is pushed. Deploying to a platform is a per-project step.

## Deploy

Any platform that runs a container works. See `.claude/skills/fastapi-model-service/references/deployment.md` for the requirements.

In short:

- Deploy the pinned SHA tag, not `latest`
- Point the platform health check at `/ping`
- Set required env vars on the platform
- Roll back by redeploying an earlier SHA tag
- Record platform quirks in your project's README, not in the template

## Known limits

- The template serves one model per service.
- It has no authentication. Add it before exposing a service publicly.
- Inference runs synchronously per request. Add a queue for long jobs.

## License

MIT. See `LICENSE`. The default model (`hustvl/yolos-tiny`) and `transformers` are Apache-2.0. Check the license of any model you swap in.