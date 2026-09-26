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

QUEUE_NAME = "analytics_queue"

CONSUMER_NAME = "analytics"

MAX_ATTEMPTS = 3


# ============================================================
# DATABASE
# ============================================================

def get_db_connection():
    return psycopg.connect(DATABASE_URL)


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

    return pika.BlockingConnection(parameters)


# ============================================================
# DATABASE CONSUMPTION RECORD
# ============================================================

def record_consumption(
    event_id,
    status,
    attempts,
    error=None
):

    consumption_id = str(uuid.uuid4())

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
                    attempts,
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
                    %s,
                    CURRENT_TIMESTAMP
                )
                """,
                (
                    consumption_id,
                    event_id,
                    CONSUMER_NAME,
                    status,
                    attempts,
                    error
                )
            )

            connection.commit()


# ============================================================
# PROCESS EVENT
# ============================================================

def process_event(event, attempt):

    event_id = event["event_id"]

    event_type = event["event_type"]

    payload = event["payload"]

    print(
        f"[ANALYTICS] Processing event: {event_id}",
        flush=True
    )

    print(
        f"[ANALYTICS] Event type: {event_type}",
        flush=True
    )

    print(
        f"[ANALYTICS] Attempt: {attempt}/{MAX_ATTEMPTS}",
        flush=True
    )

    print(
        f"[ANALYTICS] Payload: {payload}",
        flush=True
    )

    # Simulate processing time

    time.sleep(3)

    # --------------------------------------------------------
    # Permanent failure test
    # --------------------------------------------------------

    if event_type == "analytics.failure.test":

        raise RuntimeError(
            "Intentional analytics failure for recovery testing"
        )

    # --------------------------------------------------------
    # Temporary failure test
    #
    # Attempt 1 -> failure
    # Attempt 2 -> failure
    # Attempt 3 -> success
    # --------------------------------------------------------

    if event_type == "analytics.retry.test":

        if attempt < 3:

            raise RuntimeError(
                f"Temporary analytics failure on attempt {attempt}"
            )

    # --------------------------------------------------------
    # Successful processing
    # --------------------------------------------------------

    print(
        f"[ANALYTICS] Analytics processed successfully: {event_id}",
        flush=True
    )

    return True


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

        # ----------------------------------------------------
        # Decode event
        # ----------------------------------------------------

        event = json.loads(body)

        event_id = event["event_id"]

        attempt = int(
            event.get("attempt", 1)
        )

        print(
            "",
            flush=True
        )

        print(
            "========================================",
            flush=True
        )

        print(
            f"[ANALYTICS] Event: {event_id}",
            flush=True
        )

        print(
            f"[ANALYTICS] Attempt {attempt}/{MAX_ATTEMPTS}",
            flush=True
        )

        print(
            "========================================",
            flush=True
        )

        # ----------------------------------------------------
        # Process
        # ----------------------------------------------------

        process_event(
            event,
            attempt
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        record_consumption(
            event_id,
            "processed",
            attempt
        )

        channel.basic_ack(
            delivery_tag=method.delivery_tag
        )

        print(
            f"[ANALYTICS] SUCCESS: {event_id}",
            flush=True
        )

        print(
            f"[ANALYTICS] ACK: {event_id}",
            flush=True
        )

    except Exception as error:

        print(
            f"[ANALYTICS] ERROR: {error}",
            flush=True
        )

        # ----------------------------------------------------
        # No valid event
        # ----------------------------------------------------

        if event is None:

            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False
            )

            return

        event_id = event["event_id"]

        attempt = int(
            event.get("attempt", 1)
        )

        # ----------------------------------------------------
        # RETRY
        # ----------------------------------------------------

        if attempt < MAX_ATTEMPTS:

            next_attempt = attempt + 1

            print(
                f"[ANALYTICS] RETRY scheduled: "
                f"{event_id} "
                f"({next_attempt}/{MAX_ATTEMPTS})",
                flush=True
            )

            # Record failed attempt

            record_consumption(
                event_id,
                "retrying",
                attempt,
                str(error)
            )

            # Update attempt number

            event["attempt"] = next_attempt

            # Put event back into Analytics queue
            #
            # IMPORTANT:
            # We publish directly to the analytics queue.
            # This prevents Notification and Audit from
            # receiving duplicate retry messages.

            channel.basic_publish(
                exchange="",
                routing_key=QUEUE_NAME,
                body=json.dumps(event),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json"
                )
            )

            # Acknowledge original message

            channel.basic_ack(
                delivery_tag=method.delivery_tag
            )

            print(
                f"[ANALYTICS] Requeued: "
                f"{event_id} "
                f"for attempt {next_attempt}",
                flush=True
            )

        # ----------------------------------------------------
        # PERMANENT FAILURE
        # ----------------------------------------------------

        else:

            print(
                f"[ANALYTICS] Maximum attempts reached: "
                f"{event_id}",
                flush=True
            )

            record_consumption(
                event_id,
                "failed",
                attempt,
                f"Maximum attempts reached: {error}"
            )

            channel.basic_ack(
                delivery_tag=method.delivery_tag
            )

            print(
                f"[ANALYTICS] Permanently failed: {event_id}",
                flush=True
            )


# ============================================================
# START CONSUMER
# ============================================================

def start_consumer():

    print(
        "[ANALYTICS] Starting analytics consumer...",
        flush=True
    )

    while True:

        connection = None

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
            # Analytics queue
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
            # One event at a time
            # ------------------------------------------------

            channel.basic_qos(
                prefetch_count=1
            )

            # ------------------------------------------------
            # Register callback
            # ------------------------------------------------

            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=callback
            )

            print(
                "[ANALYTICS] Waiting for events...",
                flush=True
            )

            # ------------------------------------------------
            # Start consuming
            # ------------------------------------------------

            channel.start_consuming()

        except Exception as error:

            print(
                f"[ANALYTICS] Consumer connection error: {error}",
                flush=True
            )

            time.sleep(3)

        finally:

            try:

                if connection and not connection.is_closed:

                    connection.close()

            except Exception:

                pass


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    start_consumer()