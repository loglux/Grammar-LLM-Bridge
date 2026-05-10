FROM python:3.11-slim

WORKDIR /app

COPY app/ /app/app/
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Runtime configuration (OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL, etc.)
# is injected via env_file in deploy/load-balancer/docker-compose.yml.
# Do NOT bake secrets into the image.

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
