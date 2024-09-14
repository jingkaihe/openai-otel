import openai
from openai_otel import OpenAIAutoInstrumentor, tracer
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    SimpleSpanProcessor(ConsoleSpanExporter())
)

OpenAIAutoInstrumentor().instrument()


client = openai.OpenAI()

if __name__ == "__main__":
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "what's the meaning of life?"},
        ],
        # stream=True,
    )

    print(resp.choices[0].message.content)
