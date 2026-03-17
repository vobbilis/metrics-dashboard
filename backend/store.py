import uuid
from collections import deque
from datetime import UTC, datetime

from models import MetricIn, MetricOut


class MetricStore:
    def __init__(self) -> None:
        self._data: dict[str, MetricOut] = {}
        self._history: dict[str, deque[MetricOut]] = {}

    def add(self, metric: MetricIn) -> MetricOut:
        out = MetricOut(
            id=str(uuid.uuid4()),
            name=metric.name,
            value=metric.value,
            tags=metric.tags,
            timestamp=datetime.now(UTC),
        )
        self._data[metric.name] = out
        if metric.name not in self._history:
            self._history[metric.name] = deque(maxlen=20)
        self._history[metric.name].append(out)
        return out

    def all(self) -> list[MetricOut]:
        return list(self._data.values())

    def filter_by_tags(
        self,
        tags: list[tuple[str, str]],
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[MetricOut]:
        metrics = list(self._data.values())
        if tags:
            metrics = [m for m in metrics if all(m.tags.get(k) == v for k, v in tags)]
        if start is not None:
            metrics = [m for m in metrics if m.timestamp >= start]
        if end is not None:
            metrics = [m for m in metrics if m.timestamp <= end]
        return metrics

    def by_name(self, name: str) -> list[MetricOut]:
        entry = self._data.get(name)
        return [entry] if entry else []

    def history(
        self,
        name: str,
        limit: int = 20,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[MetricOut]:
        entries = self._history.get(name)
        if entries is None:
            return []
        result = list(entries)
        if start is not None:
            result = [m for m in result if m.timestamp >= start]
        if end is not None:
            result = [m for m in result if m.timestamp <= end]
        limit = max(1, min(limit, len(result) if result else 20))
        return result[-limit:]

    def delete(self, name: str) -> int:
        deleted = 1 if name in self._data else 0
        self._data.pop(name, None)
        self._history.pop(name, None)
        return deleted

    def summary(self) -> dict[str, int]:
        return {"unique_names": len(self._data), "total_data_points": len(self._data)}

    def clear(self) -> None:
        self._data = {}
        self._history = {}
