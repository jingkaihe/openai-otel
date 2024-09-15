# OpenAI OTEL

OpenAI OTEL is a library that allows you to instrument your OpenAI Python client using OpenTelemetry.

## Installation

```bash
pip install openai-otel
```

Or

```bash
poetry add openai-otel
```

if you are using poetry.


## Usage

Make sure that you have `OPENAI_API_KEY` set in your environment variables.

```python
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

resp = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "what's the meaning of life?"},
    ],
)

print(resp.choices[0].message.content)
```

## Examples

Start up tempo using docker compose:

```bash
(
    cd examples/tempo
    docker compose up -d
)
```

Run the example:

```bash
(
    cd examples/fastapi
    pip install -r requirements.txt
    fastapi run
)
```

Then open http://localhost:8000 - you shall get the meaning of life.

Afterwards you can check out the traces on Grafana. You can do it via:

* Visit http://localhost:3000
* Go to the explorer view
* Click `TraceQL`
* Run `{.service.name="fastapi-demo" && span.create.request.model="gpt-4o"}`

You will get view like this:

![alt text](./docs/grafana-screenshot.png)
