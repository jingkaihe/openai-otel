import pytest
from openai import AsyncOpenAI
from openai_otel import OpenAIAutoInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

trace.set_tracer_provider(TracerProvider())

OpenAIAutoInstrumentor().instrument()


@pytest.mark.asyncio
async def test_chat_completions_create_async():
    client = AsyncOpenAI()

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "what's the meaning of life?"},
        ],
    )

    assert resp.choices[0].message.content is not None


@pytest.mark.asyncio
async def test_chat_completions_create_with_stream_async():
    client = AsyncOpenAI()
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "what's the meaning of life?"},
        ],
        stream=True,
    )

    data = ""
    async for chunk in resp:
        if chunk.choices[0].delta.content:
            data += chunk.choices[0].delta.content

    assert data != ""

    print(data)
