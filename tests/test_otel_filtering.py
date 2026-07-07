from unittest.mock import Mock

from opentelemetry.sdk.trace.export import SpanExportResult

from selfprivacy_api.utils.otel import FilteringSpanExporter


def _span(name: str, parent=object(), attributes=None):
    span = Mock()
    span.name = name
    span.parent = parent
    span.attributes = attributes or {}
    return span


def test_is_redis_root_span_true_for_root_with_redis_prefix():
    span = _span("redis.GET", parent=None)
    assert FilteringSpanExporter._is_redis_root_span(span) is True


def test_is_redis_root_span_true_for_root_with_db_system_redis():
    span = _span("some.other.op", parent=None, attributes={"db.system": "redis"})
    assert FilteringSpanExporter._is_redis_root_span(span) is True


def test_is_redis_root_span_false_for_root_non_redis():
    span = _span("http.GET", parent=None, attributes={"db.system": "postgres"})
    assert FilteringSpanExporter._is_redis_root_span(span) is False


def test_is_redis_root_span_false_for_non_root_redis_named():
    span = _span("redis.GET", parent=object())
    assert FilteringSpanExporter._is_redis_root_span(span) is False


def test_is_redis_root_span_false_for_non_root_redis_db_system():
    span = _span("op", parent=object(), attributes={"db.system": "redis"})
    assert FilteringSpanExporter._is_redis_root_span(span) is False


def test_export_forwards_survivors_only_once():
    inner = Mock()
    inner.export.return_value = SpanExportResult.SUCCESS
    exporter = FilteringSpanExporter(inner)

    drop_a = _span("redis.GET", parent=None)
    drop_b = _span("op", parent=None, attributes={"db.system": "redis"})
    keep_root = _span("http.request", parent=None)
    keep_child = _span("redis.GET", parent=object())

    result = exporter.export([drop_a, keep_root, drop_b, keep_child])

    assert result == SpanExportResult.SUCCESS
    inner.export.assert_called_once_with([keep_root, keep_child])


def test_export_short_circuits_when_all_dropped():
    inner = Mock()
    exporter = FilteringSpanExporter(inner)

    result = exporter.export(
        [
            _span("redis.GET", parent=None),
            _span("redis.SET", parent=None),
        ]
    )

    assert result == SpanExportResult.SUCCESS
    inner.export.assert_not_called()


def test_export_returns_inner_result():
    inner = Mock()
    inner.export.return_value = SpanExportResult.FAILURE
    exporter = FilteringSpanExporter(inner)

    result = exporter.export([_span("http.request", parent=None)])

    assert result == SpanExportResult.FAILURE


def test_shutdown_delegates_to_inner_exporter():
    inner = Mock()
    exporter = FilteringSpanExporter(inner)

    exporter.shutdown()

    inner.shutdown.assert_called_once_with()


def test_force_flush_forwards_timeout_and_returns_inner_value():
    inner = Mock()
    inner.force_flush.return_value = False
    exporter = FilteringSpanExporter(inner)

    result = exporter.force_flush(1234)

    inner.force_flush.assert_called_once_with(1234)
    assert result is False


def test_force_flush_default_timeout():
    inner = Mock()
    inner.force_flush.return_value = True
    exporter = FilteringSpanExporter(inner)

    result = exporter.force_flush()

    inner.force_flush.assert_called_once_with(30000)
    assert result is True
