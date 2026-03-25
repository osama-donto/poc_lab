FROM python:3.12-slim

WORKDIR /app

# install dependencies
COPY app_test/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy worker source + reference datasets
COPY app_test/  /app/
COPY datasets/  /app/datasets/

# output dir (overrideable via OUTPUT_PATH env var)
RUN mkdir -p /app/output

ENV DATASETS_PATH=/app/datasets \
    OUTPUT_PATH=/app/output \
    TEMPORAL_HOST=temporal-frontend.temporal-system.svc.cluster.local:7233 \
    TEMPORAL_TASK_QUEUE=data-pipeline

CMD ["python", "worker.py"]
