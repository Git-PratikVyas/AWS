import os
import json
from common.dynamodb import get_item
from common.auth import check_api_key
from common.logging import setup_logger

logger = setup_logger()
TABLE = os.environ["AI_QUERIES_TABLE"]


def lambda_handler(event, context):
    if not check_api_key(event):
        return {"statusCode": 403, "body": "Forbidden"}
    query_id = event.get("pathParameters", {}).get("id")
    if not query_id:
        return {"statusCode": 400, "body": "Missing query_id"}
    item = get_item(TABLE, {"query_id": query_id})
    if not item:
        return {"statusCode": 404, "body": "Not found"}
    return {"statusCode": 200, "body": json.dumps(item)}
