import os
import sys

# Add parent directory (backend) to python path to resolve imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# --- Set Environment Variables for Mocking ---
# This must happen before any application modules are imported.
os.environ["MOCK_AWS"] = "true"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"  # Mock region
os.environ["AI_QUERIES_TABLE"] = "AIQueries"
os.environ["CUSTOMERS_TABLE"] = "Customers"
os.environ["AI_SQS_QUEUE"] = "ai-query-queue"  # Mock queue name
# Required for Salesforce polling lambda
os.environ["LAST_POLL_TIMESTAMP_PARAM"] = "/AISAAS/LastSalesforcePollTime"
# Mock secrets and credentials
os.environ["OPENAI_API_KEY"] = "MOCK_OPENAI_KEY"  # No need for a real key in mock tests
os.environ["SF_CLIENT_ID"] = "MOCK_SF_ID"
os.environ["SF_CLIENT_SECRET"] = "MOCK_SF_SECRET"
os.environ["SF_USERNAME"] = "MOCK_SF_USER"
os.environ["SF_PASSWORD"] = "MOCK_SF_PASS"
os.environ["SF_AUTH_URL"] = "http://salesforce.mock/token"


# --- Mock JWTs for RBAC Testing ---
# These tokens have a cognito:groups claim for role checking.
MOCK_ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZW1haWwiOiJhZG1pbkBleGFtcGxlLmNvbSIsImNvZ25pdG86Z3JvdXBzIjpbImFkbWlucyJdLCJpYXQiOjE1MTYyMzkwMjJ9.jIeHMGna3iih4DmwADyM0sH3P74aC4dD833H7Q9p1PA"
MOCK_USER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ODc2NTQzMjEiLCJlbWFpbCI6InVzZXJAZXhhbXBsZS5jb20iLCJjb2duaXRvOmdyb3VwcyI6WyJ1c2VycyJdLCJpYXQiOjE1MTYyMzkwMjJ9.M7GkYj4gqN4h0tXbB9TzQ0s-g8f1P5kZ6aT2eX-y8yU"


import json
from unittest.mock import patch, MagicMock

# from datetime import datetime, timezone
import boto3

# --- Imports from our application ---
from common.logging import setup_logger
from common.dynamodb import get_item, put_item
from ai_agent_lambda.handler import lambda_handler as ai_agent_handler
from ai_worker_lambda.handler import lambda_handler as ai_worker_handler
from ai_query_status_lambda.handler import lambda_handler as ai_query_status_handler
from customers_lambda.handler import lambda_handler as customers_handler
from salesforce_sync_lambda.handler import lambda_handler as salesforce_sync_handler
from salesforce_poll_lambda.handler import lambda_handler as salesforce_poll_handler


logger = setup_logger()


def create_mock_table(table_name):
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

        if table_name == os.environ["CUSTOMERS_TABLE"]:
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[{"AttributeName": "Id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "Id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )
        elif table_name == os.environ["AI_QUERIES_TABLE"]:
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


def setup_mock_environment():
    """Creates mock DynamoDB tables for the test run."""
    print("--- Setting up mock environment ---")
    create_mock_table("AIQueries")
    create_mock_table("Customers")
    print("Mock tables created.")


@patch("common.openai_agent.openai.ChatCompletion.create")
def test_ai_flow(mock_openai_create):
    """Tests the full asynchronous AI query flow."""
    print("\n--- Testing AI Query Flow ---")

    # 1. Configure the mock to return a simple dictionary, not a MagicMock
    mock_openai_create.return_value = {
        "choices": [{"message": {"content": "This is a mock AI response."}}]
    }

    # 2. Submit AI query
    logger.info("1. Submitting AI query")
    event = {"body": json.dumps({"prompt": "Hello, AI!"})}
    response = ai_agent_handler(event, None)
    assert response["statusCode"] == 202
    print("AI Agent Response:", response)
    query_id = json.loads(response["body"])["query_id"]

    # 3. Simulate AI Worker processing SQS
    logger.info("2. Simulating AI Worker processing (with OpenAI call mocked)")
    mock_sqs_message_body = json.dumps({"query_id": query_id, "prompt": "Hello, AI!"})
    event = {"Records": [{"body": mock_sqs_message_body}]}
    ai_worker_handler(event, None)
    print("AI Worker processed the message.")

    # 4. Check AI query status
    logger.info("3. Checking AI query status")
    event_status = {"pathParameters": {"id": query_id}}
    status_response = ai_query_status_handler(event_status, None)
    print("AI Query Status Response:", status_response)

    body = json.loads(status_response["body"])
    assert status_response["statusCode"] == 200
    assert body["status"] == "COMPLETED"
    assert body["response"] == "This is a mock AI response."


@patch("common.auth.decode_jwt")
def test_rbac_flow(mock_decode_jwt):
    """Tests Role-Based Access Control on protected endpoints."""
    print("\n--- Testing RBAC Flow ---")

    # Define what the mock should return based on the token it receives.
    # This bypasses the actual JWT signature verification for the test.
    def side_effect(token):
        if token == MOCK_ADMIN_TOKEN:
            return {"cognito:groups": ["admins"]}
        if token == MOCK_USER_TOKEN:
            return {"cognito:groups": ["users"]}
        return None

    mock_decode_jwt.side_effect = side_effect

    # Case 1: Admin user attempts to access the sync endpoint (should succeed)
    logger.info("1. Testing access for ADMIN user (should SUCCEED)")
    admin_event = {"headers": {"Authorization": f"Bearer {MOCK_ADMIN_TOKEN}"}}
    # We patch the Salesforce call since we're only testing RBAC logic here
    with patch("salesforce_sync_lambda.handler.fetch_customers", return_value=[]):
        response = salesforce_sync_handler(admin_event, None)
        print("Admin Response:", response)
        assert response["statusCode"] == 200

    # Case 2: Regular user attempts to access (should be forbidden)
    logger.info("2. Testing access for REGULAR user (should be FORBIDDEN)")
    user_event = {"headers": {"Authorization": f"Bearer {MOCK_USER_TOKEN}"}}
    response = salesforce_sync_handler(user_event, None)
    print("User Response:", response)
    assert response["statusCode"] == 403

    # Case 3: Unauthenticated user attempts to access (should be forbidden)
    logger.info("3. Testing access for NO AUTH user (should be FORBIDDEN)")
    no_auth_event = {"headers": {}}
    response = salesforce_sync_handler(no_auth_event, None)
    print("No Auth Response:", response)
    assert response["statusCode"] == 403


@patch("salesforce_poll_lambda.handler.get_dynamodb_table")
@patch("salesforce_poll_lambda.handler.requests.get")
@patch("salesforce_poll_lambda.handler.get_salesforce_token")
@patch("salesforce_poll_lambda.handler.ssm")
def test_salesforce_poll_flow(
    mock_ssm, mock_get_sf_token, mock_requests_get, mock_get_table
):
    """Tests the scheduled Salesforce polling flow using mocks."""
    print("\n--- Testing Salesforce Poll Flow ---")

    # 1. Setup mocks for external dependencies
    logger.info("1. Setting up mocks for Salesforce, SSM, and DynamoDB")
    mock_ssm.get_parameter.return_value = {
        "Parameter": {"Value": "2023-01-01T00:00:00Z"}
    }
    mock_get_sf_token.return_value = ("mock-token", "http://salesforce.mock")
    mock_sf_response = MagicMock()
    mock_sf_response.json.return_value = {
        "records": [
            {"Id": "SF001", "Name": "Updated Corp"},
            {"Id": "SF002", "Name": "New LLC"},
        ]
    }
    mock_sf_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_sf_response

    # Setup mock for the DynamoDB table and its batch_writer context manager
    mock_table = MagicMock()
    mock_batch_writer = MagicMock()
    mock_table.batch_writer.return_value.__enter__.return_value = mock_batch_writer
    mock_get_table.return_value = mock_table

    # 2. Execute the polling handler
    logger.info("2. Executing the polling handler")
    response = salesforce_poll_handler({}, None)
    print("Poll Handler Response:", response)
    assert response["statusCode"] == 200
    assert "Successfully synced 2 records" in response["body"]

    # 3. Verify the mock interactions
    logger.info("3. Verifying mock calls")
    mock_table.batch_writer.assert_called_once()
    assert mock_batch_writer.put_item.call_count == 2
    mock_batch_writer.put_item.assert_any_call(
        Item={"Id": "SF001", "Name": "Updated Corp"}
    )
    mock_ssm.put_parameter.assert_called_once()


@patch("salesforce_sync_lambda.handler.is_admin", return_value=True)
@patch("salesforce_sync_lambda.handler.put_item")
@patch("salesforce_sync_lambda.handler.fetch_customers")
def test_salesforce_sync_flow(mock_fetch_customers, mock_put_item, mock_is_admin):
    """Tests the manual Salesforce sync flow logic."""
    print("\n--- Testing Salesforce Sync Flow ---")

    # 1. Arrange
    logger.info("1. Setting up mocks for manual Salesforce sync")
    mock_fetch_customers.return_value = [
        {"Id": "SF_MANUAL_01", "Name": "Manual Sync Corp"},
    ]
    admin_event = {"headers": {"Authorization": "Bearer any-admin-token"}}

    # 2. Act
    logger.info("2. Executing the manual sync handler")
    response = salesforce_sync_handler(admin_event, None)
    print("Sync Handler Response:", response)

    # 3. Assert
    logger.info("3. Verifying mock calls and response")
    assert response["statusCode"] == 200
    assert "Successfully synced 1 customers" in response["body"]
    mock_fetch_customers.assert_called_once()
    mock_put_item.assert_called_once_with(
        os.environ["CUSTOMERS_TABLE"],
        {"Id": "SF_MANUAL_01", "Name": "Manual Sync Corp"},
    )


def test_customers_flow():
    """Tests adding and fetching customers."""
    print("\n--- Testing Customers Flow ---")
    logger.info("1. Adding and fetching customers")
    put_item(
        "Customers", {"Id": "CUST01", "Name": "Alice", "Email": "alice@example.com"}
    )
    put_item("Customers", {"Id": "CUST02", "Name": "Bob", "Email": "bob@example.com"})

    # Corrected to pass two arguments as the handler expects
    customers_response = customers_handler({}, None)
    print("Customers Response:", customers_response)
    assert customers_response["statusCode"] == 200
    assert len(json.loads(customers_response["body"])) >= 2


if __name__ == "__main__":
    setup_mock_environment()
    test_ai_flow()
    test_rbac_flow()
    test_salesforce_poll_flow()
    test_salesforce_sync_flow()
    test_customers_flow()
    print("\n--- All mock tests completed successfully! ---")
