# Cloud Event-Driven Processing Platform

A production-style event-driven processing platform built with **FastAPI, RabbitMQ, PostgreSQL, Python workers, React, and Docker Compose**.

The platform demonstrates how a single event can be published once and independently consumed by multiple services through a **RabbitMQ fanout exchange**, with persistent processing state, retry handling, failure tracking, and a live React dashboard.

---

## 🚀 What This Project Demonstrates

This project focuses on practical distributed-systems and cloud-engineering concepts:

- Event-driven architecture
- Asynchronous service communication
- RabbitMQ fanout exchanges
- Multiple independent consumers
- PostgreSQL event persistence
- Consumer-level processing state
- Automatic retry handling
- Failure tracking
- Dockerized microservices
- REST APIs with FastAPI
- React monitoring dashboard
- Event inspection and publishing
- Horizontal consumer scaling

The key architectural idea is simple:

> **Publish an event once, then allow multiple independent services to react to it.**

---

## 🏗️ Architecture

```text
                         ┌─────────────────────┐
                         │    React Dashboard   │
                         │   Publish / Monitor  │
                         └──────────┬──────────┘
                                    │
                                    │ HTTP
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │        API          │
                         └──────────┬──────────┘
                                    │
                       ┌────────────┴────────────┐
                       │                         │
                       ▼                         ▼
              ┌─────────────────┐      ┌─────────────────┐
              │   PostgreSQL    │      │    RabbitMQ     │
              │  Event Storage  │      │ Fanout Exchange │
              └─────────────────┘      └────────┬────────┘
                                                │
                         ┌──────────────────────┼──────────────────────┐
                         │                      │                      │
                         ▼                      ▼                      ▼
                ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
                │ Notification   │    │   Analytics    │    │     Audit      │
                │    Worker      │    │    Worker      │    │    Worker      │
                └───────┬────────┘    └───────┬────────┘    └───────┬────────┘
                        │                     │                     │
                        └─────────────────────┼─────────────────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │   PostgreSQL    │
                                     │    Consumer     │
                                     │    Records      │
                                     └─────────────────┘
```

---

## 🔄 Event Flow

When an event is published:

```text
1. User publishes event
          │
          ▼
2. FastAPI receives event
          │
          ├──────────────► PostgreSQL
          │                 Stores event
          │
          ▼
3. RabbitMQ fanout exchange
          │
          ├──────────────► Notification Worker
          │
          ├──────────────► Analytics Worker
          │
          └──────────────► Audit Worker
                              │
                              ▼
                       Processing result
                              │
                              ▼
                         PostgreSQL
                              │
                              ▼
                       React Dashboard
```

Each consumer has its own queue and processes the event independently.

Adding another consumer does not require changing the publisher.

---

## 🧩 Why Fanout?

A RabbitMQ **fanout exchange** broadcasts a message to every queue bound to that exchange.

For example:

```text
                    order.created
                          │
                          ▼
                  ┌──────────────┐
                  │   RabbitMQ   │
                  │Fanout Exchange│
                  └───────┬──────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        Notification   Analytics      Audit
          Queue         Queue         Queue
```

This makes the architecture loosely coupled.

The publisher does not need to know:

- Which consumers exist
- How many consumers exist
- How each consumer processes the event

---

## ⚙️ Core Components

### FastAPI API

Responsible for:

- Publishing events
- Storing events
- Returning event history
- Returning event details
- Providing dashboard statistics
- Initializing RabbitMQ exchange configuration

### RabbitMQ

Responsible for:

- Event distribution
- Fanout messaging
- Independent consumer queues
- Asynchronous communication

### Notification Worker

Processes notification-related events independently.

### Analytics Worker

Processes analytics events and demonstrates:

- Retry handling
- Attempt tracking
- Temporary failures
- Permanent failures

### Audit Worker

Processes events independently for audit purposes.

### PostgreSQL

Stores:

- Events
- Event payloads
- Event status
- Consumer processing status
- Retry attempts
- Errors
- Processing timestamps

### React Dashboard

Provides:

- Event publishing
- Live dashboard statistics
- Consumer statistics
- Recent events
- Event inspection
- Processing status
- Retry/failure visibility

---

## 🔁 Retry & Failure Handling

The Analytics consumer supports a maximum of **3 attempts**.

Example:

```text
Attempt 1
    │
    ▼
Retrying
    │
    ▼
Attempt 2
    │
    ▼
Retrying
    │
    ▼
Attempt 3
    │
    ▼
Processed
```

If all attempts fail:

```text
Attempt 1
    │
    ▼
Retrying
    │
    ▼
Attempt 2
    │
    ▼
Retrying
    │
    ▼
Attempt 3
    │
    ▼
Failed
```

The retry attempt is persisted in PostgreSQL so the dashboard can display the processing history.

---

## 🧪 Failure Testing

The project includes an intentional failure event:

```text
analytics.failure.test
```

Example payload:

```json
{
  "test_id": "FAIL-001",
  "message": "Testing analytics recovery"
}
```

The Analytics worker records the failure while the Notification and Audit consumers continue processing the same event independently.

---

## 🔄 Retry Testing

Publish:

```text
analytics.retry.test
```

Example payload:

```json
{
  "test_id": "RETRY-003",
  "message": "Testing automatic retry and recovery"
}
```

The Analytics consumer retries the event until the configured maximum attempt count is reached.

---

## 📊 Dashboard

The React dashboard provides visibility into the event-processing system.

### Dashboard capabilities

- Total events
- Processed events
- Failed events
- Retrying events
- Consumer statistics
- Recent events
- Event status
- Event inspection
- Consumer processing details
- Browser-based event publishing
- Automatic dashboard refresh

### Event Inspector

Selecting an event displays:

- Event ID
- Event type
- Event payload
- Overall event status
- Notification status
- Analytics status
- Audit status
- Processing attempts
- Errors
- Processing timestamps

---

## 📡 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | API health check |
| POST | `/events` | Publish a new event |
| GET | `/events` | List recent events |
| GET | `/events/{event_id}` | Inspect an event and consumer results |
| GET | `/dashboard` | Dashboard statistics |

### Example Event

```json
{
  "event_type": "order.created",
  "payload": {
    "order_id": "ORD-1002",
    "customer": "customer-001",
    "amount": 2500
  }
}
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| API | FastAPI + Uvicorn |
| Messaging | RabbitMQ |
| Database | PostgreSQL 17 |
| Workers | Python + Pika |
| HTTP Client | Axios |
| Icons | Lucide React |
| Containers | Docker |
| Orchestration | Docker Compose |

---

## 📁 Project Structure

```text
cloud-event-platform
│
├── api
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app
│       └── main.py
│
├── consumers
│   │
│   ├── notification
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app
│   │       └── worker.py
│   │
│   ├── analytics
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app
│   │       └── worker.py
│   │
│   └── audit
│       ├── Dockerfile
│       ├── requirements.txt
│       └── app
│           └── worker.py
│
├── database
│   └── init.sql
│
├── frontend
│   ├── src
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── public
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── docker-compose.yml
└── README.md
```

---

## 🐳 Running the Backend

From the project root:

```powershell
docker compose up -d --build
```

Check the containers:

```powershell
docker compose ps
```

Expected services:

```text
event-platform-postgres
event-platform-rabbitmq
event-platform-api
event-platform-notification
event-platform-analytics
event-platform-audit
```

---

## 🌐 Services

### FastAPI

```text
http://localhost:8030
```

Swagger documentation:

```text
http://localhost:8030/docs
```

Health check:

```text
http://localhost:8030/health
```

### RabbitMQ Management

```text
http://localhost:15672
```

Development credentials configured by Docker Compose:

```text
Username: guest
Password: guest
```

### React Dashboard

From the project root:

```powershell
cd frontend
npm install
npm run dev
```

Dashboard:

```text
http://localhost:5173
```

---

## 🧪 Quick Test

### 1. Start the platform

```powershell
docker compose up -d --build
```

### 2. Start the frontend

```powershell
cd frontend
npm run dev
```

### 3. Open the dashboard

```text
http://localhost:5173
```

### 4. Publish an event

Use:

```text
Event Type:
order.created
```

Payload:

```json
{
  "order_id": "ORD-1002",
  "customer": "customer-001",
  "amount": 2500
}
```

### 5. Inspect the result

The Event Inspector should show processing information for:

```text
Notification
Analytics
Audit
```

---

## 🆚 Event-Driven Architecture vs Job Queue

This project is intentionally different from a traditional background job queue.

### Job Queue

```text
Job
 │
 ▼
Worker
```

A job is normally consumed by one worker.

### Event-Driven Fanout

```text
Event
 │
 ▼
RabbitMQ Exchange
 │
 ├──── Consumer A
 │
 ├──── Consumer B
 │
 └──── Consumer C
```

The same event can independently trigger multiple services.

This makes the event-driven model useful for systems where one business event can have several independent side effects.

---

## 🔐 Reliability Concepts

The implementation demonstrates:

- Persistent event storage
- Independent consumer queues
- Consumer-level status tracking
- Retry attempts
- Failure recording
- Asynchronous processing
- Service isolation
- Containerized deployment
- Monitoring through a dashboard

---

## 🚀 Possible Future Improvements

Potential extensions include:

- Dead-letter queues
- RabbitMQ publisher confirms
- Idempotent consumers
- Event schema validation
- Event replay
- Distributed tracing
- Prometheus metrics
- Grafana dashboards
- Authentication and authorization
- Kubernetes deployment
- Horizontal worker autoscaling
- Cloud deployment
- Kafka-based streaming implementation

---

## 🎯 Project Goal

The goal of this project is to demonstrate how cloud applications can move from tightly coupled request/response communication toward asynchronous, event-driven processing.

The architecture provides a foundation for systems such as:

- Order processing
- Notification pipelines
- Audit systems
- Analytics pipelines
- Payment workflows
- Logistics systems
- Microservice platforms

---

## 👨‍💻 Author

**Rishi Pilla**

Cloud Engineering Portfolio Project — 2026

GitHub: [@rishipilla](https://github.com/rishipilla)

---

## 📄 License

This project is intended as a portfolio and learning project.
