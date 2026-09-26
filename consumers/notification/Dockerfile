FROM python:3.12-slim

WORKDIR /app

COPY consumers/notification/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY consumers/notification/app ./app

CMD ["python", "app/worker.py"]