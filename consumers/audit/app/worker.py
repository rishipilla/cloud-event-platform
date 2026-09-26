import json
import os
import time
import uuid

import pika
import psycopg


# ============================================================
# CONFIGURATION
# ============================================================

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

QUEUE_NAME = "audit_queue"

CONSUMER_NAME = "audit"


# ============================================================
# DATABASE
# ============================================================

def get_db_connection():
    return psycopg.connect(
        DATABASE_URL
    )


# ============================================================
# RABBITMQ
# ============================================================

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

    return pika.BlockingConnection(
        parameters
    )


# ============================================================
# RECORD CONSUMPTION
# ============================================================

def record_consumption(
    event_id,
    status,
    error=None
):

    consumption_id = str(
        uuid.uuid4()
    )

    with get_db_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO event_consumptions
                (
                    id,
                    event_id,
                    consumer,
                    status,
                    error,
                    processed_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP
                )
                """,
                (
                    consumption_id,
                    event_id,
                    CONSUMER_NAME,
                    status,
                    error
                )
            )

            connection.commit()


# ============================================================
# PROCESS EVENT
# ============================================================

def process_event(event):

    event_id = event["event_id"]

    event_type = event["event_type"]

    payload = event["payload"]

    print(
        f"[AUDIT] Received event: {event_id}",
        flush=True
    )

    print(
        f"[AUDIT] Event type: {event_type}",
        flush=True
    )

    print(
        f"[AUDIT] Payload: {payload}",
        flush=True
    )

    # Simulate audit logging

    time.sleep(2)

    print(
        f"[AUDIT] Audit record created for event: {event_id}",
        flush=True
    )


# ============================================================
# RABBITMQ CALLBACK
# ============================================================

def callback(
    channel,
    method,
    properties,
    body
):

    event = None

    try:

        event = json.loads(
            body
        )

        event_id = event["event_id"]

        process_event(
            event
        )

        record_consumption(
            event_id,
            "processed"
        )

        channel.basic_ack(
            delivery_tag=method.delivery_tag
        )

        print(
            f"[AUDIT] ACK: {event_id}",
            flush=True
        )

    except Exception as error:

        print(
            f"[AUDIT] Processing failed: {error}",
            flush=True
        )

        if event:

            record_consumption(
                event["event_id"],
                "failed",
                str(error)
            )

        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False
        )


# ============================================================
# START CONSUMER
# ============================================================

def start_consumer():

    print(
        "[AUDIT] Starting audit consumer...",
        flush=True
    )

    while True:

        try:

            connection = get_rabbitmq_connection()

            channel = connection.channel()

            # ------------------------------------------------
            # Exchange
            # ------------------------------------------------

            channel.exchange_declare(
                exchange=EXCHANGE_NAME,
                exchange_type="fanout",
                durable=True
            )

            # ------------------------------------------------
            # Queue
            # ------------------------------------------------

            channel.queue_declare(
                queue=QUEUE_NAME,
                durable=True
            )

            # ------------------------------------------------
            # Bind queue
            # ------------------------------------------------

            channel.queue_bind(
                exchange=EXCHANGE_NAME,
                queue=QUEUE_NAME
            )

            # ------------------------------------------------
            # Process one event at a time
            # ------------------------------------------------

            channel.basic_qos(
                prefetch_count=1
            )

            # ------------------------------------------------
            # Consume
            # ------------------------------------------------

            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=callback
            )

            print(
                "[AUDIT] Waiting for events...",
                flush=True
            )

            channel.start_consuming()

        except Exception as error:

            print(
                f"[AUDIT] Consumer error: {error}",
                flush=True
            )

            time.sleep(3)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    start_consumer()