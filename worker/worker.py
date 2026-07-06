import json
import os
import threading
import time

import psycopg2
import uvicorn
from fastapi import FastAPI
from confluent_kafka import Consumer

app = FastAPI()
DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    for attempt in range(10):
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS signup_counts (
                        day DATE PRIMARY KEY,
                        count INT NOT NULL
                    )
                """)
                conn.commit()
            return
        except psycopg2.OperationalError:
            time.sleep(2)
    raise RuntimeError("Postgres never became available")


def consume():
    consumer = Consumer({
        "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"],
        "group.id": "signup-workers",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe(["signups"])
    conn = get_conn()
    conn.autocommit = True
    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue
        event = json.loads(msg.value())
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO signup_counts (day, count) VALUES (%s, 1)
                ON CONFLICT (day) DO UPDATE SET count = signup_counts.count + 1
            """, (event["date"],))
        consumer.commit(msg)


@app.get("/aggregation")
def get_aggregation():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT day, count FROM signup_counts")
        rows = cur.fetchall()
    return {str(day): count for day, count in rows}


if __name__ == "__main__":
    init_db()
    threading.Thread(target=consume, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8001)