---
name: fastapi-model-service
description: Use when building, adapting, or debugging a FastAPI service that serves an ML model (vision, NLP, tabular) in a Docker container with GitHub Actions CI. Triggers on "serve a model", "deploy a model API", "swap the model", "add an endpoint", "adapt the template", "scaffold a model service", and deployment or health-check failures.
---

# Workflow
1. Read the repo structure and README before changing anything.
2. If the request does not state the model, input type, and output shape, ask. Otherwise proceed.
3. Change only the swap points below.
4. Run `pytest tests/unit`, then run the app locally and call `/health` and `/ping`.
5. Confirm the Dockerfile still bakes the weights at build time.
6. Report: files changed, why, and what to verify in CI.

# Swap points (edit these only)
- `app/services/inference_service.py`: load and run the model
- `app/schemas/`: request and response shapes
- `app/config.py`: model name and path
- `requirements.txt`: pinned, minimal dependencies
- `Dockerfile`: the weight download line only
- `tests/`: update tests and test assets to match the new output shape

# Adding an endpoint
1. New file in `app/routers/`, registered in `app/main.py`.
2. Logic in a new function in `app/services/`, not in the router.
3. Request and response Pydantic models in `app/schemas/`.
4. Unit test and integration test for it.

# Never change without asking
- Lifespan loading and the `app.state` pattern
- Readiness logic: `/ping` returns 503 until the model is loaded
- `/health` stays informational (status, model_loaded, model name)
- Workflow job order and SHA plus `latest` tagging
- Base image and `CMD` in the Dockerfile

If a request requires changing one of these, stop and explain why before editing.

# Architecture rules
- Load the model once in lifespan, never per request.
- Routers stay thin. Services never import FastAPI.
- Never return the model object or any non-JSON type in a response.
- Validate inputs: file type, size limit, clear 4xx errors.
- Return JSON with stable field names, documented by Pydantic models.
- No secrets in the image. Use env vars.
- Keep dependencies minimal. Image size drives cold start time.

# Definition of done
- `pytest tests/unit` passes
- `/health` reports `model_loaded: true` and `/ping` returns 200
- Integration tests exist for every new endpoint and skip unless `BASE_URL` is set
- README lists curl examples for every endpoint

# References (read only when relevant)
- `references/failure-patterns.md`: read when debugging
- `references/deployment.md`: read when preparing or changing deployment