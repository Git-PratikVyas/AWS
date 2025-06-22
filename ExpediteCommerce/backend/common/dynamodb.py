import os
import boto3

MOCK_AWS = os.environ.get("MOCK_AWS", "false").lower() == "true"
CUSTOMERS_TABLE = os.environ.get("CUSTOMERS_TABLE", "Customers")
AI_QUERIES_TABLE = os.environ.get("AI_QUERIES_TABLE", "AIQueries")


def get_table(table_name):
    if MOCK_AWS:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            endpoint_url="http://127.0.0.1:4566",  # "http://host.docker.internal:4566",
        )

        try:
            table = dynamodb.Table(table_name)
            table.load()
            print(f"Table {table_name} already exists.")
        except dynamodb.meta.client.exceptions.ResourceNotFoundException:
            print(f"Creating table {table_name}...")

            if table_name == CUSTOMERS_TABLE:
                table = dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[{"AttributeName": "Id", "KeyType": "HASH"}],
                    AttributeDefinitions=[
                        {"AttributeName": "Id", "AttributeType": "S"}
                    ],
                    BillingMode="PAY_PER_REQUEST",
                )
            elif table_name == AI_QUERIES_TABLE:
                table = dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[{"AttributeName": "query_id", "KeyType": "HASH"}],
                    AttributeDefinitions=[
                        {"AttributeName": "query_id", "AttributeType": "S"}
                    ],
                    BillingMode="PAY_PER_REQUEST",
                )
            else:
                raise ValueError(f"Table {table_name} not found")

            table.wait_until_exists()
            print(f"Table {table_name} created.")

    else:
        dynamodb = boto3.resource(
            "dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )

    return dynamodb.Table(table_name)


def put_item(table_name, item):
    table = get_table(table_name)
    table.put_item(Item=item)


def get_item(table_name, key):
    table = get_table(table_name)
    response = table.get_item(Key=key)
    return response.get("Item")


def scan_table(table_name):
    table = get_table(table_name)
    return table.scan().get("Items", [])


def get_dynamodb_table(table_name):
    """Returns a Boto3 DynamoDB Table resource."""
    # In a real app with LocalStack, you might add endpoint_url logic here
    # based on an environment variable, but for mock this is sufficient.
    dynamodb_resource = boto3.resource("dynamodb")
    return dynamodb_resource.Table(table_name)
