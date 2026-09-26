FROM python:3.12-slim

WORKDIR /app

COPY consumers/audit/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY consumers/audit/app ./app

CMD ["python", "app/worker.py"]