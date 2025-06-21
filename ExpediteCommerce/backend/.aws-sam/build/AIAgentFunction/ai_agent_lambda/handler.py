import json
import os
import uuid
import boto3
from common.dynamodb import put_item
from common.auth import check_api_key
from common.logging import setup_logger

logger = setup_logger()
# sqs = boto3.client("sqs")

QUEUE_URL = os.environ["AI_SQS_QUEUE"]
TABLE = os.environ["AI_QUERIES_TABLE"]


def lambda_handler(event, context):
    logger.info("----handler start: ai_agent_lambda")
    if not check_api_key(event):
        return {"statusCode": 403, "body": "Forbidden"}

    logger.info(f"----body start: {event}")

    body = json.loads(event.get("body") or "{}")

    logger.info(f"----body: {body}")

    prompt = body.get("prompt")
    logger.info(f"----prompt: {prompt}")
    if not prompt:
        return {"statusCode": 400, "body": "Missing prompt"}

    query_id = str(uuid.uuid4())
    # Store initial status in DynamoDB
    put_item(TABLE, {"query_id": query_id, "prompt": prompt, "status": "QUEUED"})
    # # Enqueue the request
    # sqs.send_message(
    #     QueueUrl=QUEUE_URL,
    #     MessageBody=json.dumps({"query_id": query_id, "prompt": prompt}),
    # )

    MOCK_AWS = os.environ.get("MOCK_AWS", "false").lower() == "true"
    if MOCK_AWS:
        print("----MOCK_AWS_LocalStack---")
        sqs = boto3.client(
            "sqs",
            region_name="us-east-1",
            endpoint_url="http://127.0.0.1:4566",  # "http://host.docker.internal:4566",
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
        QUEUE_URL = "ai-query-queue"
        response = sqs.create_queue(QueueName=QUEUE_URL)
        print(f"Que created {response['QueueUrl']}")

    else:
        sqs = boto3.client("sqs")

    # Enqueue the request
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps({"query_id": query_id, "prompt": prompt}),
    )

    logger.info(f"\nEnqueued AI query: {query_id}")
    return {
        "statusCode": 202,
        "body": json.dumps({"query_id": query_id, "status": "QUEUED"}),
    }
