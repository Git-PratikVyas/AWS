import os
import json
from common.dynamodb import scan_table
from common.auth import check_api_key
from common.logging import setup_logger

logger = setup_logger()
TABLE = os.environ["CUSTOMERS_TABLE"]


def lambda_handler(event, context):
    if not check_api_key(event):
        return {"statusCode": 403, "body": "Forbidden"}
    items = scan_table(TABLE)
    return {"statusCode": 200, "body": json.dumps(items)}
