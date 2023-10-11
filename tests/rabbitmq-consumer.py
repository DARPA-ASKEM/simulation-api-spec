import os
import logging

import pika

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

RABBITMQ_USERNAME = os.environ["RABBITMQ_USERNAME"]
RABBITMQ_PASSWORD = os.environ["RABBITMQ_PASSWORD"]
RABBITMQ_HOST = os.environ["RABBITMQ_HOST"]
RABBITMQ_PORT = os.environ["RABBITMQ_PORT"]

creds = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
conn_config = pika.ConnectionParameters(
    host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=creds
)


def mock_rabbitmq_consumer():
    connection = pika.BlockingConnection(conn_config)
    channel = connection.channel()

    channel.queue_declare(queue="simulation-status")

    def callback(ch, method, properties, body):
        resp = json.loads(body)
        logging.info("job_id:%s; progress:%s", resp["job_id"], resp["progress"])

    channel.basic_consume(
        queue="simulation-status", on_message_callback=callback, auto_ack=True
    )

    logging.info(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()
