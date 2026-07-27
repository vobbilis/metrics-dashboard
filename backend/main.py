import asyncio
import csv
import io
import json
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import psutil
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from alert_store import AlertStore
from models import (
    AlertEvent,
    AlertRuleIn,
    AlertRuleOut,
    AlertRuleUpdate,
    MetricIn,
    MetricOut,
    MetricSummary,
)
from store import MetricStore

store = MetricStore()
alert_store = AlertStore()


logger = logging.getLogger(__name__)


async def _collect_host_metrics() -> None:
    """Collect real host metrics (CPU, memory, disk) every 5 seconds."""
    psutil.cpu_percent()  # prime the first reading
    await asyncio.sleep(1)
    while True:
        try:
            store.add(
                MetricIn(
                    name="cpu_percent",
                    value=psutil.cpu_percent(),
                    tags={"source": "host"},
                )
            )
            store.add(
                MetricIn(
                    name="memory_percent",
                    value=psutil.virtual_memory().percent,
                    tags={"source": "host"},
                )
            )
            store.add(
                MetricIn(
                    name="disk_percent",
                    value=psutil.disk_usage("/").percent,
                    tags={"source": "host"},
                )
            )
        except Exception:
            logger.exception("Error collecting host metrics")
        await asyncio.sleep(5)


async def _evaluate_loop() -> None:
    while True:
        await asyncio.sleep(10)
        try:
            alert_store.evaluate(store)
        except Exception:
            logger.exception("Error during alert evaluation")


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    eval_task = asyncio.create_task(_evaluate_loop())
    collector_task = asyncio.create_task(_collect_host_metrics())
    yield
    eval_task.cancel()
    collector_task.cancel()
    for t in [eval_task, collector_task]:
        try:
            await t
        except asyncio.CancelledError:
            pass


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    value = value.replace(" ", "+")
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid datetime format '{value}'. " "Use ISO-8601 (e.g., '2026-03-15T14:00:00')."
            ),
        )


app = FastAPI(title="Metrics Dashboard API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/metrics", response_model=MetricOut, status_code=201)
def submit_metric(metric: MetricIn) -> MetricOut:
    return store.add(metric)


@app.get("/metrics", response_model=list[MetricOut])
def list_metrics(
    tag: list[str] = Query(default=[]),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
) -> list[MetricOut]:
    parsed_tags: list[tuple[str, str]] = []
    for t in tag:
        if ":" not in t:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tag format '{t}'. Expected 'key:value'.",
            )
        key, value = t.split(":", 1)
        parsed_tags.append((key, value))
    return store.filter_by_tags(parsed_tags, _parse_dt(start), _parse_dt(end))


@app.get("/metrics/summary", response_model=MetricSummary)
def metrics_summary() -> MetricSummary:
    data = store.summary()
    return MetricSummary(**data)


@app.get("/metrics/export")
def export_metrics(
    format: str = "csv",
    tag: list[str] = Query(default=[]),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
) -> StreamingResponse:
    if format != "csv":
        raise HTTPException(status_code=400, detail="Unsupported format. Use format=csv")

    # Parse tag filters (same logic as list_metrics)
    parsed_tags: list[tuple[str, str]] = []
    for t in tag:
        if ":" not in t:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tag format '{t}'. Expected 'key:value'.",
            )
        key, value = t.split(":", 1)
        parsed_tags.append((key, value))

    # Get metrics filtered by tags and time range
    metrics = store.filter_by_tags(parsed_tags, _parse_dt(start), _parse_dt(end))

    # Write to CSV buffer
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["id", "name", "value", "tags", "timestamp"])

    # Write data rows
    for metric in metrics:
        writer.writerow(
            [metric.id, metric.name, metric.value, json.dumps(metric.tags), metric.timestamp]
        )

    # Return streaming response
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="metrics.csv"'},
    )


@app.get("/metrics/{name}/history", response_model=list[MetricOut])
def get_metric_history(
    name: str,
    limit: int = 20,
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
) -> list[MetricOut]:
    results = store.history(name, limit, _parse_dt(start), _parse_dt(end))
    if not results:
        raise HTTPException(status_code=404, detail=f"No history found for '{name}'")
    return results


@app.get("/metrics/{name}", response_model=list[MetricOut])
def get_metric(name: str) -> list[MetricOut]:
    results = store.by_name(name)
    if not results:
        raise HTTPException(status_code=404, detail=f"No metrics found for '{name}'")
    return results


@app.delete("/metrics/{name}")
def delete_metric(name: str) -> dict[str, int]:
    deleted = store.delete(name)
    alerts_deleted = alert_store.delete_rules_by_metric_name(name)
    return {"deleted": deleted, "alerts_deleted": alerts_deleted}


@app.post("/alerts", response_model=AlertRuleOut, status_code=201)
def create_alert(rule: AlertRuleIn) -> AlertRuleOut:
    return alert_store.add_rule(rule)


@app.get("/alerts", response_model=list[AlertRuleOut])
def list_alerts() -> list[AlertRuleOut]:
    return alert_store.all_rules()


@app.get("/alerts/events", response_model=list[AlertEvent])
def list_alert_events() -> list[AlertEvent]:
    return alert_store.all_events()


@app.put("/alerts/{rule_id}", response_model=AlertRuleOut)
def update_alert(rule_id: str, update: AlertRuleUpdate) -> AlertRuleOut:
    result = alert_store.update_rule(rule_id, update)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Alert rule '{rule_id}' not found")
    return result


@app.delete("/alerts/{rule_id}")
def delete_alert(rule_id: str) -> dict[str, int]:
    deleted = alert_store.delete_rule(rule_id)
    return {"deleted": deleted}
