import os
import json
import boto3
from datetime import datetime, timedelta, timezone
import requests
from urllib.parse import urlencode

# Assuming these common functions exist and are accessible
from common.salesforce import get_salesforce_token
from common.dynamodb import get_dynamodb_table

# Name for the SSM parameter that stores the last poll timestamp
SSM_PARAM_NAME = os.environ.get(
    "LAST_POLL_TIMESTAMP_PARAM", "/AISAAS/LastSalesforcePollTime"
)
CUSTOMERS_TABLE_NAME = os.environ.get("CUSTOMERS_TABLE", "Customers")

ssm = boto3.client("ssm")


def get_last_poll_time():
    """Gets the last poll timestamp from SSM Parameter Store."""
    try:
        param = ssm.get_parameter(Name=SSM_PARAM_NAME, WithDecryption=False)
        return param["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        # If parameter is not found, default to 1 day ago and create it
        print(f"SSM Parameter {SSM_PARAM_NAME} not found. Defaulting to 1 day ago.")
        one_day_ago = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        update_last_poll_time(one_day_ago)
        return one_day_ago


def update_last_poll_time(timestamp_str):
    """Updates the last poll timestamp in SSM Parameter Store."""
    print(f"Updating last poll time in SSM to: {timestamp_str}")
    ssm.put_parameter(
        Name=SSM_PARAM_NAME, Value=timestamp_str, Type="String", Overwrite=True
    )


def lambda_handler(event, context):
    """
    This function polls Salesforce for recently updated customer records
    and syncs them to DynamoDB. It's triggered by a schedule.
    """
    print("Starting Salesforce poll...")
    current_time = datetime.now(timezone.utc)
    last_poll_time = get_last_poll_time()

    try:
        token, instance_url = get_salesforce_token()

        # SOQL query for recently modified accounts. Format is YYYY-MM-DDThh:mm:ssZ
        soql_query = f"SELECT Id, Name, Type, Industry, AnnualRevenue FROM Account WHERE LastModifiedDate > {last_poll_time}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        query_params = urlencode({"q": soql_query})
        sf_url = f"{instance_url}/services/data/v58.0/query/?{query_params}"

        print(f"Querying Salesforce for records modified after: {last_poll_time}")
        resp = requests.get(sf_url, headers=headers)
        resp.raise_for_status()

        records = resp.json().get("records", [])
        print(f"Found {len(records)} records to update.")

        if records:
            customers_table = get_dynamodb_table(CUSTOMERS_TABLE_NAME)
            with customers_table.batch_writer() as batch:
                for record in records:
                    item = {
                        k: v
                        for k, v in record.items()
                        if v is not None and k != "attributes"
                    }
                    batch.put_item(Item=item)
            print(f"Successfully synced {len(records)} records to DynamoDB.")

        # On success (even if no records), update the poll time for the next run
        update_last_poll_time(current_time.isoformat())

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": f"Successfully synced {len(records)} records."}
            ),
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        # Do not update poll time on failure, so the next run retries from the same point
        raise e
