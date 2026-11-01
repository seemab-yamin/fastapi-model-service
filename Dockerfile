FROM runpod/base:0.4.0-cuda11.8.0

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY models ./models
COPY app ./app


# ARG MODEL_NAME=hustvl/yolos-tiny
# ENV MODEL_NAME=${MODEL_NAME}
# ENV HF_HOME=/app/.cache/huggingface
# RUN python -c "import os; from transformers import pipeline; pipeline('object-detection', model=os.environ['MODEL_NAME'])"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
