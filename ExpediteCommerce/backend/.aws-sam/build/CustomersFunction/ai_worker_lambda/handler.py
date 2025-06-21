import json
import os
from common.dynamodb import put_item
from common.openai_agent import process_query
from common.logging import setup_logger

logger = setup_logger()
TABLE = os.environ["AI_QUERIES_TABLE"]


def lambda_handler(event, context):
    logger.info("handler start: ai_worker_lambda")
    for record in event["Records"]:
        body = json.loads(record["body"])
        query_id = body["query_id"]
        prompt = body["prompt"]
        try:
            # Fetch dataset from DynamoDB or use a mock
            dataset = "Sample customer data from DynamoDB"
            ai_response = process_query(prompt, dataset)
            put_item(
                TABLE,
                {
                    "query_id": query_id,
                    "prompt": prompt,
                    "response": ai_response,
                    "status": "COMPLETED",
                },
            )
            logger.info(f"Processed AI query: {query_id}")
        except Exception as e:
            put_item(
                TABLE,
                {
                    "query_id": query_id,
                    "prompt": prompt,
                    "status": "FAILED",
                    "error": str(e),
                },
            )
            logger.error(f"Failed to process AI query {query_id}: {e}")
