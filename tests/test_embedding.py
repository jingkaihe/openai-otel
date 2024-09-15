import pytest
import openai
from openai_otel import OpenAIAutoInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from openai import AsyncOpenAI

trace.set_tracer_provider(TracerProvider())

OpenAIAutoInstrumentor().instrument()


def test_embedding_create():
    client = openai.OpenAI()
    resp = client.embeddings.create(
        input="Hello, world!",
        model="text-embedding-ada-002",
    )

    assert resp.data[0].embedding is not None


@pytest.mark.asyncio
async def test_embedding_create_async():
    client = AsyncOpenAI()
    resp = await client.embeddings.create(
        input="Hello, world!",
        model="text-embedding-ada-002",
    )

    assert resp.data[0].embedding is not None
