import json
import os
import uuid

import pika
import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(
    title="Cloud Event-Driven Processing API",
    version="1.0.0",
    description="API for publishing and monitoring events."
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/eventplatform"
)

RABBITMQ_HOST = os.getenv(
    "RABBITMQ_HOST",
    "localhost"
)

RABBITMQ_PORT = int(
    os.getenv("RABBITMQ_PORT", "5672")
)

RABBITMQ_USER = os.getenv(
    "RABBITMQ_USER",
    "guest"
)

RABBITMQ_PASSWORD = os.getenv(
    "RABBITMQ_PASSWORD",
    "guest"
)

EXCHANGE_NAME = "events"


class EventRequest(BaseModel):
    event_type: str
    payload: dict


def get_db_connection():
    return psycopg.connect(DATABASE_URL)


def get_rabbitmq_connection():

    credentials = pika.PlainCredentials(
        RABBITMQ_USER,
        RABBITMQ_PASSWORD
    )

    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials
    )

    return pika.BlockingConnection(parameters)


def setup_exchange():

    connection = get_rabbitmq_connection()

    channel = connection.channel()

    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="fanout",
        durable=True
    )

    connection.close()


@app.get("/health")
def health():

    return {
        "service": "event-platform-api",
        "status": "healthy"
    }


@app.post("/events")
def create_event(data: EventRequest):

    event_id = str(uuid.uuid4())

    try:

        with get_db_connection() as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO events
                    (
                        id,
                        event_type,
                        payload,
                        status
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        event_id,
                        data.event_type,
                        json.dumps(data.payload),
                        "published"
                    )
                )

                connection.commit()


        rabbitmq_connection = get_rabbitmq_connection()

        channel = rabbitmq_connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type="fanout",
            durable=True
        )


        event_message = {

            "event_id": event_id,

            "event_type": data.event_type,

            "payload": data.payload
        }


        channel.basic_publish(

            exchange=EXCHANGE_NAME,

            routing_key="",

            body=json.dumps(event_message),

            properties=pika.BasicProperties(

                delivery_mode=2,

                content_type="application/json"
            )
        )


        rabbitmq_connection.close()


        return {

            "event_id": event_id,

            "event_type": data.event_type,

            "status": "published",

            "message": "Event published successfully"
        }


    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=f"Failed to publish event: {str(error)}"
        )


@app.get("/events")
def list_events():

    try:

        with get_db_connection() as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        event_type,
                        payload,
                        status,
                        created_at
                    FROM events
                    ORDER BY created_at DESC
                    LIMIT 100
                    """
                )

                events = cursor.fetchall()


        return {

            "count": len(events),

            "events": [

                {

                    "event_id": str(event[0]),

                    "event_type": event[1],

                    "payload": event[2],

                    "status": event[3],

                    "created_at": event[4]

                }

                for event in events

            ]
        }


    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=f"Failed to retrieve events: {str(error)}"
        )


@app.get("/events/{event_id}")
def get_event(event_id: str):

    try:

        with get_db_connection() as connection:

            with connection.cursor() as cursor:

                # ---------------------------------
                # Get event
                # ---------------------------------

                cursor.execute(
                    """
                    SELECT
                        id,
                        event_type,
                        payload,
                        status,
                        created_at
                    FROM events
                    WHERE id = %s
                    """,
                    (event_id,)
                )

                event = cursor.fetchone()


                if event is None:

                    raise HTTPException(
                        status_code=404,
                        detail="Event not found"
                    )


                # ---------------------------------
                # Get consumer processing records
                # ---------------------------------

                cursor.execute(
                    """
                    SELECT
                        consumer,
                        status,
                        attempts,
                        error,
                        processed_at
                    FROM event_consumptions
                    WHERE event_id = %s
                    ORDER BY processed_at DESC NULLS LAST
                    """,
                    (event_id,)
                )

                consumptions = cursor.fetchall()


        consumers = [

            {
                "consumer": row[0],
                "status": row[1],
                "attempts": row[2],
                "error": row[3],
                "processed_at": row[4]
            }

            for row in consumptions

        ]


        return {

            "event_id": str(event[0]),

            "event_type": event[1],

            "payload": event[2],

            "status": event[3],

            "created_at": event[4],

            "consumers": consumers

        }


    except HTTPException:

        raise


    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=f"Failed to retrieve event: {str(error)}"
        )


@app.get("/dashboard")
def dashboard():

    try:

        with get_db_connection() as connection:

            with connection.cursor() as cursor:

                # ---------------------------------
                # Event totals
                # ---------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM events
                    """
                )

                total_events = cursor.fetchone()[0]


                # ---------------------------------
                # Fully processed events
                # ---------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM events e
                    WHERE
                        (
                            SELECT COUNT(*)
                            FROM event_consumptions ec
                            WHERE ec.event_id = e.id
                              AND ec.status = 'processed'
                        ) >= 3
                    """
                )

                processed_events = cursor.fetchone()[0]


                # ---------------------------------
                # Failed consumer processing
                # ---------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT event_id)
                    FROM event_consumptions
                    WHERE status = 'failed'
                    """
                )

                failed_events = cursor.fetchone()[0]


                # ---------------------------------
                # Retrying events
                # ---------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT event_id)
                    FROM event_consumptions
                    WHERE status = 'retrying'
                    """
                )

                retrying_events = cursor.fetchone()[0]


                # ---------------------------------
                # Consumer statistics
                # ---------------------------------

                cursor.execute(
                    """
                    SELECT
                        consumer,

                        COUNT(*) FILTER (
                            WHERE status = 'processed'
                        ) AS processed,

                        COUNT(*) FILTER (
                            WHERE status = 'failed'
                        ) AS failed,

                        COUNT(*) FILTER (
                            WHERE status = 'retrying'
                        ) AS retrying

                    FROM event_consumptions

                    GROUP BY consumer

                    ORDER BY consumer
                    """
                )

                consumer_rows = cursor.fetchall()


                consumers = [

                    {
                        "consumer": row[0],
                        "processed": row[1],
                        "failed": row[2],
                        "retrying": row[3]
                    }

                    for row in consumer_rows

                ]


                # ---------------------------------
                # Recent event status
                # ---------------------------------

                cursor.execute(
                    """
                    SELECT
                        e.id,
                        e.event_type,
                        e.created_at,

                        COUNT(
                            DISTINCT ec.consumer
                        ) AS consumer_count,

                        COUNT(
                            DISTINCT CASE
                                WHEN ec.status = 'processed'
                                THEN ec.consumer
                            END
                        ) AS processed_count,

                        COUNT(
                            DISTINCT CASE
                                WHEN ec.status = 'failed'
                                THEN ec.consumer
                            END
                        ) AS failed_count,

                        COUNT(
                            DISTINCT CASE
                                WHEN ec.status = 'retrying'
                                THEN ec.consumer
                            END
                        ) AS retrying_count

                    FROM events e

                    LEFT JOIN event_consumptions ec
                        ON ec.event_id = e.id

                    GROUP BY
                        e.id,
                        e.event_type,
                        e.created_at

                    ORDER BY
                        e.created_at DESC

                    LIMIT 100
                    """
                )

                recent_rows = cursor.fetchall()


                recent_events = []


                for row in recent_rows:

                    event_id = str(row[0])

                    event_type = row[1]

                    created_at = row[2]

                    consumer_count = row[3]

                    processed_count = row[4]

                    failed_count = row[5]

                    retrying_count = row[6]


                    if failed_count > 0:

                        status = "failed"

                    elif retrying_count > 0:

                        status = "retrying"

                    elif processed_count >= 3:

                        status = "processed"

                    elif consumer_count > 0:

                        status = "processing"

                    else:

                        status = "published"


                    recent_events.append(

                        {
                            "event_id": event_id,
                            "event_type": event_type,
                            "status": status,
                            "consumer_count": consumer_count,
                            "processed_count": processed_count,
                            "failed_count": failed_count,
                            "retrying_count": retrying_count,
                            "created_at": created_at
                        }

                    )


        return {

            "total_events": total_events,

            "processed_events": processed_events,

            "failed_events": failed_events,

            "retrying_events": retrying_events,

            "consumers": consumers,

            "recent_events": recent_events

        }


    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=f"Failed to load dashboard metrics: {str(error)}"
        )


@app.on_event("startup")
def startup():

    try:

        setup_exchange()

        print(
            "[API] RabbitMQ exchange initialized",
            flush=True
        )

    except Exception as error:

        print(
            f"[API] RabbitMQ initialization failed: {error}",
            flush=True
        )