import os
import json
from common.logging import setup_logger

logger = setup_logger()

os.environ["MOCK_AWS"] = "true"
# os.environ["AI_SQS_QUEUE"] = "http://localhost:4566/000000000000/ai-query-queue"
os.environ["AI_QUERIES_TABLE"] = "AIQueries"
os.environ["CUSTOMERS_TABLE"] = "Customers"
os.environ["AI_SQS_QUEUE"] = "ai-query-queue"

os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

os.environ["OPENAI_API_KEY"] = "test_openai_api_key"

from ai_agent_lambda.handler import lambda_handler as ai_agent_handler
from ai_worker_lambda.handler import lambda_handler as ai_worker_handler
from ai_query_status_lambda.handler import lambda_handler as ai_query_status_handler
from customers_lambda.handler import lambda_handler as customers_handler
from common.dynamodb import put_item


def test_end_to_end():
    # 1. Submit AI query
    logger.info("1. Submit AI query")
    event = {"body": json.dumps({"prompt": "Hello, AI!"})}
    response = ai_agent_handler(event, None)
    print("AI Agent Response:", response)
    query_id = json.loads(response["body"])["query_id"]

    # 2. Simulate AI Worker processing SQS
    logger.info("2. Simulate AI Worker processing SQS")
    mock_record = {
        "body": json.dumps(
            {
                "query_id": query_id,
                "prompt": json.loads(event["body"])["prompt"],
                "response": response,
                "status": "COMPLETED",
            }
        )
    }
    event = {"Records": [mock_record]}

    ai_worker_handler(event, None)

    # 3. Check AI query status
    logger.info("3. Check AI query status")
    event_status = {"pathParameters": {"id": query_id}}
    status_response = ai_query_status_handler(event_status, None)
    print("AI Query Status Response:", status_response)

    # 4. Add and fetch customers
    logger.info("4. Add and fetch customers")
    put_item("Customers", {"Id": "1", "Name": "Alice", "Email": "alice@example.com"})
    put_item("Customers", {"Id": "2", "Name": "Bob", "Email": "bob@example.com"})
    customers_response = customers_handler({})
    print("Customers Response:", customers_response)


if __name__ == "__main__":
    print("----test_end_to_end----")
    test_end_to_end()
