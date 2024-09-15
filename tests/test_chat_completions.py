import pytest
import openai
from openai_otel import OpenAIAutoInstrumentor, tracer
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

trace.set_tracer_provider(TracerProvider())

OpenAIAutoInstrumentor().instrument()


def test_chat_completions_create():
    client = openai.OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "what's the meaning of life?"},
        ],
    )

    assert resp.choices[0].message.content is not None


def test_chat_completions_create_with_stream():
    client = openai.OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "what's the meaning of life?"},
        ],
        stream=True,
    )

    data = ""
    for chunk in resp:
        if chunk.choices[0].delta.content:
            data += chunk.choices[0].delta.content

    assert data != ""
