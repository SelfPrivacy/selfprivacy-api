"""GraphQL API for SelfPrivacy."""

# pylint: disable=too-few-public-methods
from inspect import isawaitable
from typing import Any, Callable

from opentelemetry import context as otel_context, trace
from strawberry.extensions import LifecycleStep, SchemaExtension
from strawberry.extensions.tracing import OpenTelemetryExtension
from strawberry.extensions.tracing.utils import should_skip_tracing
from strawberry.permission import BasePermission
from strawberry.types import Info

from selfprivacy_api.actions.api_tokens import is_token_valid
from selfprivacy_api.utils.localization import Localization
from selfprivacy_api.utils.request_memo import begin_request_memo, end_request_memo


class IsAuthenticated(BasePermission):
    """Is authenticated permission"""

    message = "You must be authenticated to access this resource."

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        token = info.context["request"].headers.get("Authorization")
        if token is None:
            token = info.context["request"].query_params.get("token")
        if token is None:
            connection_params = info.context.get("connection_params")
            if connection_params is not None:
                token = connection_params.get("Authorization")
        if token is None:
            return False
        return is_token_valid(token.replace("Bearer ", ""))


class LocaleExtension(SchemaExtension):
    """Parse the Accept-Language header and set the locale in the context as one of the supported locales."""

    def resolve(self, _next, root, info: Info, *args, **kwargs):
        locale = Localization().get_locale(
            info.context["request"].headers.get("Accept-Language")
        )
        info.context["locale"] = locale
        return _next(root, info, *args, **kwargs)


class SelfPrivacyOpenTelemetryExtension(OpenTelemetryExtension):
    def on_operation(self):
        server_span = trace.get_current_span()
        gen = super().on_operation()
        next(gen)

        token = otel_context.attach(
            trace.set_span_in_context(self._span_holder[LifecycleStep.OPERATION])
        )
        try:
            yield
        finally:
            otel_context.detach(token)
            try:
                next(gen)
            except StopIteration:
                pass

        operation_name = self.execution_context.operation_name
        if operation_name and server_span and server_span.is_recording():
            server_span.update_name(f"GraphQL {operation_name}")
            server_span.set_attribute("graphql.operation.name", operation_name)

    async def resolve(
        self,
        _next: Callable,
        root: Any,
        info: Any,
        *args: str,
        **kwargs: Any,
    ) -> Any:
        if should_skip_tracing(_next, info):
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                result = await result

            return result

        with self._tracer.start_as_current_span(
            f"GraphQL Resolving: {info.field_name}",
        ) as span:
            self.add_tags(span, info, kwargs)
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                result = await result

            return result


class RequestMemoExtension(SchemaExtension):
    """Gives each GraphQL operation a memoization scope"""

    def on_operation(self):
        token = begin_request_memo()
        try:
            yield
        finally:
            end_request_memo(token)
