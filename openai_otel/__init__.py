from opentelemetry.trace import get_tracer, Span
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from functools import wraps
from typing import Collection
import json
from openai.types.chat import ChatCompletion
from openai.resources.chat import AsyncCompletions, Completions
from openai.resources.embeddings import (
    AsyncEmbeddings,
    Embeddings,
    CreateEmbeddingResponse,
)

# xxx: maybe a dedicated __version__.py file?
__version__ = "0.1.0.alpha2"

tracer = get_tracer(__name__, __version__)


class OpenAIAutoInstrumentor(BaseInstrumentor):
    def _instrument(self, **kwargs):
        self.original_completions_create = Completions.create
        self.original_completions_create_async = AsyncCompletions.create
        self.original_embeddings_create = Embeddings.create
        self.original_embeddings_create_async = AsyncEmbeddings.create

        Completions.create = self._patch_completions(
            "openai.completions.create",
            self.original_completions_create,
        )

        AsyncCompletions.create = self._patch_completions_async(
            "openai.completions.create_async",
            self.original_completions_create_async,
        )

        Embeddings.create = self._patch_embeddings(
            "openai.embeddings.create",
            self.original_embeddings_create,
        )

        AsyncEmbeddings.create = self._patch_embeddings_async(
            "openai.embeddings.create_async",
            self.original_embeddings_create_async,
        )

    def _patch_embeddings(self, span_name, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                self._track_req(kwargs, span)
                resp: CreateEmbeddingResponse = func(*args, **kwargs)
                self._track_embeddings_resp(resp, span)
                return resp

        return wrapper

    def _patch_embeddings_async(self, span_name, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                self._track_req(kwargs, span)
                resp: CreateEmbeddingResponse = await func(*args, **kwargs)
                self._track_embeddings_resp(resp, span)
                return resp

        return wrapper

    def _patch_completions(self, span_name, func):
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
                                self._track_completions_resp(chunk, span)
                                tracked = True
                            if chunk.choices[0].delta.content:
                                data += chunk.choices[0].delta.content
                            yield chunk
                        span.set_attribute("create.response.message.content", data)

                    return gen()
                else:
                    self._track_req(kwargs, span)
                    resp: ChatCompletion = func(*args, **kwargs)
                    self._track_completions_resp(resp, span)
                    return resp

        return wrapper

    def _patch_completions_async(self, span_name, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                stream = kwargs.get("stream", False)
                if stream:

                    async def gen():
                        data = ""
                        tracked = False
                        async for chunk in await func(*args, **kwargs):
                            if not tracked:
                                self._track_completions_resp(chunk, span)
                                tracked = True
                            if chunk.choices[0].delta.content:
                                data += chunk.choices[0].delta.content
                            yield chunk
                        span.set_attribute("create.response.message.content", data)

                    return gen()
                else:
                    self._track_req(kwargs, span)
                    resp: ChatCompletion = await func(*args, **kwargs)
                    self._track_completions_resp(resp, span)
                    return resp

        return wrapper

    def _track_req(self, kwargs: dict, span: Span):
        span_prefix = "create.request"
        for k, v in kwargs.items():
            if isinstance(v, (int, float, str, bool)):
                span.set_attribute(f"{span_prefix}.{k}", v)
            elif isinstance(v, (dict, list)):
                span.set_attribute(f"{span_prefix}.{k}", json.dumps(v))

    def _track_completions_resp(self, resp: ChatCompletion, span: Span):
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

    def _track_embeddings_resp(self, resp: CreateEmbeddingResponse, span: Span):
        span_resp_prefix = "create.response"
        span.set_attribute(f"{span_resp_prefix}.model", resp.model)

        if resp.usage:
            span.set_attribute(
                f"{span_resp_prefix}.usage.prompt_tokens",
                resp.usage.prompt_tokens,
            )
            span.set_attribute(
                f"{span_resp_prefix}.usage.total_tokens",
                resp.usage.total_tokens,
            )

    def instrumentation_dependencies(self) -> Collection[str]:
        return ["openai"]

    def _uninstrument(self, **kwargs):
        Completions.create = self.original_completions_create
        AsyncCompletions.create = self.original_completions_create_async
        Embeddings.create = self.original_embeddings_create
        AsyncEmbeddings.create = self.original_embeddings_create_async
