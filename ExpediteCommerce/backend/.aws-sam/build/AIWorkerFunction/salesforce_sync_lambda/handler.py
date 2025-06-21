import os
import json
from common.salesforce import fetch_customers
from common.dynamodb import put_item
from common.auth import is_admin
from common.logging import setup_logger

logger = setup_logger()


def lambda_handler(event, context):
    """
    Handles manual Salesforce sync requests.
    Only allows access to users with the 'admins' role.
    """
    if not is_admin(event):
        return {
            "statusCode": 403,
            "body": json.dumps(
                {"error": "Forbidden: Access is restricted to administrators."}
            ),
        }

    try:
        customers = fetch_customers()
        table_name = os.environ["CUSTOMERS_TABLE"]
        for customer in customers:
            put_item(table_name, customer)

        logger.info(f"Synced {len(customers)} customers from Salesforce.")
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": f"Successfully synced {len(customers)} customers."}
            ),
        }
    except Exception as e:
        logger.error(f"Error during Salesforce sync: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
