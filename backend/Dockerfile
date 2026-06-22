FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN groupadd --system collector && useradd --system --gid collector collector
COPY --chown=collector:collector app ./app
ENV PYTHONPATH=/app
USER collector
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
