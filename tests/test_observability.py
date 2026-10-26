from agentops.observability import MetricsRecorder, StructuredLogger, Tracer


def test_tracer_records_nested_spans_with_correct_parents():
    tracer = Tracer()
    with tracer.span("outer"):
        with tracer.span("inner"):
            pass

    tree = tracer.as_tree()
    assert len(tree) == 2
    outer, inner = tree
    assert outer["parent_id"] is None
    assert inner["parent_id"] == outer["span_id"]


def test_tracer_marks_span_as_error_on_exception():
    tracer = Tracer()
    try:
        with tracer.span("failing"):
            raise ValueError("boom")
    except ValueError:
        pass
    assert tracer.as_tree()[0]["status"] == "error"


def test_tracer_records_duration():
    tracer = Tracer()
    with tracer.span("timed"):
        pass
    assert tracer.as_tree()[0]["duration_seconds"] >= 0


def test_metrics_recorder_counters():
    metrics = MetricsRecorder()
    metrics.increment("calls")
    metrics.increment("calls")
    metrics.increment("calls", value=3)
    assert metrics.summary()["counters"]["calls"] == 5


def test_metrics_recorder_latency_summary():
    metrics = MetricsRecorder()
    for v in [0.1, 0.2, 0.3, 0.4, 0.5]:
        metrics.record_latency("op", v)
    summary = metrics.summary()["latencies"]["op"]
    assert summary["count"] == 5
    assert abs(summary["mean_seconds"] - 0.3) < 1e-9
    assert summary["p50_seconds"] == 0.3


def test_structured_logger_records_and_filters_errors():
    logger = StructuredLogger()
    logger.log("started")
    logger.log("failed", level="error", reason="bad input")
    assert len(logger.events) == 2
    errors = logger.errors()
    assert len(errors) == 1
    assert errors[0]["reason"] == "bad input"
