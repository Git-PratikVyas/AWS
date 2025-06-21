import openai
import os

openai.api_key = os.environ.get("OPENAI_API_KEY")


def process_query(prompt, dataset):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant for our SaaS platform. Analyze user queries and the provided data to give customer insight.",
            },
            {"role": "user", "content": f"{prompt}\n\nDataset: {dataset}"},
        ],
    )
    return response["choices"][0]["message"]["content"]
