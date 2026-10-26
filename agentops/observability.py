"""Structured logging, metrics, and span-based tracing for an agent run --
"add logging, metrics, and tracing so others can see what your agent did,
what it cost, and whether it is still healthy."
"""
from __future__ import annotations

import itertools
import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class Span:
    span_id: int
    parent_id: int | None
    name: str
    start_time: float
    end_time: float | None = None
    status: str = "ok"
    attributes: dict = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float | None:
        if self.end_time is None:
            return None
        return self.end_time - self.start_time


class Tracer:
    """Collects a tree of spans for one agent run."""

    def __init__(self):
        self._id_counter = itertools.count(1)
        self.spans: list[Span] = []
        self._active_parent: int | None = None

    @contextmanager
    def span(self, name: str, **attributes):
        span_id = next(self._id_counter)
        parent_id = self._active_parent
        record = Span(span_id=span_id, parent_id=parent_id, name=name, start_time=time.perf_counter(), attributes=dict(attributes))
        self.spans.append(record)

        previous_parent = self._active_parent
        self._active_parent = span_id
        try:
            yield record
        except Exception:
            record.status = "error"
            raise
        finally:
            record.end_time = time.perf_counter()
            self._active_parent = previous_parent

    def as_tree(self) -> list[dict]:
        """A flat list of span records, each carrying its parent id, suitable
        for reconstructing the call tree or exporting to a trace viewer."""
        return [
            {
                "span_id": s.span_id, "parent_id": s.parent_id, "name": s.name,
                "duration_seconds": s.duration_seconds, "status": s.status,
                "attributes": s.attributes,
            }
            for s in self.spans
        ]


class MetricsRecorder:
    """A small in-memory metrics store: counters and latency samples per named metric."""

    def __init__(self):
        self._counters: dict[str, float] = {}
        self._latencies: dict[str, list[float]] = {}

    def increment(self, name: str, value: float = 1.0) -> None:
        self._counters[name] = self._counters.get(name, 0.0) + value

    def record_latency(self, name: str, seconds: float) -> None:
        self._latencies.setdefault(name, []).append(seconds)

    def summary(self) -> dict:
        latency_summary = {}
        for name, samples in self._latencies.items():
            sorted_samples = sorted(samples)
            n = len(sorted_samples)
            latency_summary[name] = {
                "count": n,
                "mean_seconds": sum(sorted_samples) / n,
                "p50_seconds": sorted_samples[int(0.5 * (n - 1))],
                "p95_seconds": sorted_samples[int(0.95 * (n - 1))],
            }
        return {"counters": dict(self._counters), "latencies": latency_summary}


class StructuredLogger:
    """An in-memory structured (JSON-shaped) log, so tests can assert on
    recorded events without parsing stdout; a real deployment would also
    write these records to stdout or a log sink."""

    def __init__(self):
        self.events: list[dict] = []

    def log(self, event: str, level: str = "info", **fields) -> dict:
        record = {"timestamp": time.time(), "level": level, "event": event, **fields}
        self.events.append(record)
        return record

    def errors(self) -> list[dict]:
        return [e for e in self.events if e["level"] == "error"]
