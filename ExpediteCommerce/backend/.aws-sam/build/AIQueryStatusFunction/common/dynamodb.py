import os
import boto3

MOCK_AWS = os.environ.get("MOCK_AWS", "false").lower() == "true"
CUSTOMERS_TABLE = os.environ.get("CUSTOMERS_TABLE", "Customers")
AI_QUERIES_TABLE = os.environ.get("AI_QUERIES_TABLE", "AIQueries")

# if MOCK_AWS:
#     # In-memory mock database
#     _mock_db = {}

#     def get_table(table_name):
#         return table_name

#     def put_item(table_name, item):
#         if table_name not in _mock_db:
#             _mock_db[table_name] = []
#         _mock_db[table_name].append(item)

#     def get_item(table_name, key):
#         for item in _mock_db.get(table_name, []):
#             if all(item.get(k) == v for k, v in key.items()):
#                 return item
#         return None

#     def scan_table(table_name):
#         return _mock_db.get(table_name, [])
# else:
#     import boto3

# dynamodb = boto3.resource(
#     "dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1")
# )

# dynamodb = boto3.resource(
#     "dynamodb",
#     region_name=os.environ.get("AWS_REGION", "us-east-1"),
#     endpoint_url="http://host.docker.internal:4566"
#     if os.environ.get("MOCK_AWS") == "true"
#     else None,
# )

# if MOCK_AWS:
#     dynamodb = boto3.resource(
#         "dynamodb",
#         region_name=os.environ.get("AWS_REGION", "us-east-1"),
#         endpoint_url="http://host.docker.internal:4566",
#     )

#     try:
#         table = dynamodb.Table(table_name)
#         table.load()
#         print(f"Table {table_name} already exists.")
#     except dynamodb.meta.client.exceptions.ResourceNotFoundException:
#         print(f"Creating table {table_name}...")
#         table = dynamodb.create_table(
#             TableName=table_name,
#             KeySchema=[{"AttributeName": "Id", "KeyType": "HASH"}],
#             AttributeDefinitions=[{"AttributeName": "Id", "AttributeType": "S"}],
#             BillingMode="PAY_PER_REQUEST",
#         )
#         table.wait_until_exists()
#         print(f"Table {table_name} created.")

# else:
#     dynamodb = boto3.resource(
#         "dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1")
#     )


# def get_table(table_name):
#     return dynamodb.Table(table_name)


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
