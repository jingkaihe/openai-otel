from opentelemetry.trace import get_tracer, Span
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from functools import wraps
import openai
from typing import Collection
import json
from openai.types.chat import ChatCompletion

# xxx: maybe a dedicated __version__.py file?
__version__ = "0.1.0"

tracer = get_tracer(__name__, __version__)


class OpenAIAutoInstrumentor(BaseInstrumentor):
    def _instrument(self, **kwargs):
        self.original_chat_completions_create = openai.chat.completions.create

        openai.chat.completions.create = self._patch_chat_completions_create(
            "openai.chat.completions.create",
            self.original_chat_completions_create,
        )

    def _patch_chat_completions_create(self, span_name, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                stream = kwargs.get("stream", False)
                if stream:

                    def gen():
                        data = ""
                        tracked = False
                        for chunk in func(*args, **kwargs):
                            if not tracked:
                                self._track_resp(chunk, span)
                                tracked = True
                            if chunk.choices[0].delta.content:
                                data += chunk.choices[0].delta.content
                            yield chunk
                        span.set_attribute("create.response.message.content", data)

                    return gen()
                else:
                    self._track_req(kwargs, span)
                    resp: ChatCompletion = func(*args, **kwargs)
                    self._track_resp(resp, span)
                    return resp

        return wrapper

    def _track_req(self, kwargs: dict, span: Span):
        span_prefix = "create.request"
        for k, v in kwargs.items():
            if isinstance(v, (int, float, str, bool)):
                span.set_attribute(f"{span_prefix}.{k}", v)
            elif isinstance(v, (dict, list)):
                span.set_attribute(f"{span_prefix}.{k}", json.dumps(v))

    def _track_resp(self, resp: ChatCompletion, span: Span):
        span_resp_prefix = "create.response"
        if resp.usage:
            span.set_attribute(
                f"{span_resp_prefix}.usage.prompt_tokens",
                resp.usage.prompt_tokens,
            )
            span.set_attribute(
                f"{span_resp_prefix}.usage.completion_tokens",
                resp.usage.completion_tokens,
            )
            span.set_attribute(
                f"{span_resp_prefix}.usage.total_tokens",
                resp.usage.total_tokens,
            )

        span.set_attributes(
            {
                f"{span_resp_prefix}.model": resp.model,
                f"{span_resp_prefix}.id": resp.id,
            }
        )

        span.set_attribute(span_resp_prefix, resp.model_dump_json())

    def instrumentation_dependencies(self) -> Collection[str]:
        return ["openai"]

    def _uninstrument(self, **kwargs):
        openai.chat.completions.create = self.original_chat_completions_create
