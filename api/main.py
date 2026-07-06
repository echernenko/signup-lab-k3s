import json
import os
from datetime import date

from fastapi import FastAPI
from confluent_kafka import Producer

app = FastAPI()
producer = Producer({"bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"]})


@app.get("/signup")
def signup(country: str):
    today = date.today().isoformat()
    event = {"country": country, "date": today}
    producer.produce("signups", key=country, value=json.dumps(event))
    producer.flush()
    return {"status": "queued", "country": country, "date": today}