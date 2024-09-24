from openai_otel import OpenAIAutoInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
import os

resource = Resource(
    attributes={SERVICE_NAME: os.getenv("SERVICE_NAME", "langchain-demo")}
)
provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
    insecure=True,
)
processor = BatchSpanProcessor(exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
from langchain_openai import ChatOpenAI

OpenAIAutoInstrumentor().instrument()

llm = ChatOpenAI(model="gpt-4o", temperature=1)

print(llm.invoke("What is the meaning of life?"))
