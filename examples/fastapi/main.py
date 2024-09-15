import openai
from openai_otel import OpenAIAutoInstrumentor, tracer
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from fastapi import FastAPI
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
import os

resource = Resource(
    attributes={SERVICE_NAME: os.getenv("SERVICE_NAME", "fastapi-demo")}
)
provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
    insecure=True,
)
processor = BatchSpanProcessor(exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

app = FastAPI()


@app.get("/")
async def root():
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "what's the meaning of life?"},
        ],
    )
    return resp.choices[0].message.content


OpenAIAutoInstrumentor().instrument()
FastAPIInstrumentor().instrument_app(app)
