from __future__ import annotations

from dataclasses import dataclass

from agent.tool_api import JsonDict, tool


@dataclass(frozen=True, slots=True)
class Task:
    id: str
    title: str
    hours: float
    value: float

    @property
    def density(self) -> float:
        if self.hours <= 0:
            return self.value
        return self.value / self.hours


def _as_float(value: object, *, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number") from exc
    if parsed < 0:
        raise ValueError(f"{field} must be non-negative")
    return parsed


def _load_tasks(raw_tasks: object) -> list[Task]:
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise ValueError("tasks must be a non-empty list")

    tasks: list[Task] = []
    seen: set[str] = set()
    for index, raw_task in enumerate(raw_tasks, start=1):
        if not isinstance(raw_task, dict):
            raise ValueError("each task must be an object")
        title = str(raw_task.get("title") or raw_task.get("name") or f"Task {index}").strip()
        task_id = str(raw_task.get("id") or title.lower().replace(" ", "_") or index).strip()
        if task_id in seen:
            task_id = f"{task_id}_{index}"
        seen.add(task_id)

        hours = _as_float(raw_task.get("hours"), field=f"tasks[{index}].hours")
        value = _as_float(
            raw_task.get("value", raw_task.get("priority", 1)),
            field=f"tasks[{index}].value",
        )
        if hours <= 0:
            raise ValueError(f"tasks[{index}].hours must be greater than zero")
        tasks.append(Task(id=task_id, title=title, hours=hours, value=value))
    return tasks


def _serialize_task(task: Task) -> JsonDict:
    return {
        "id": task.id,
        "title": task.title,
        "hours": task.hours,
        "value": task.value,
        "value_per_hour": round(task.density, 3),
    }


def _summarize(tasks: list[Task], available_hours: float) -> JsonDict:
    used_hours = sum(task.hours for task in tasks)
    total_value = sum(task.value for task in tasks)
    return {
        "selected_tasks": [_serialize_task(task) for task in tasks],
        "used_hours": round(used_hours, 2),
        "free_hours": round(max(available_hours - used_hours, 0), 2),
        "total_value": round(total_value, 2),
        "task_count": len(tasks),
    }


def _baseline_greedy(tasks: list[Task], available_hours: float) -> list[Task]:
    selected: list[Task] = []
    used = 0.0
    for task in sorted(tasks, key=lambda item: (-item.density, -item.value, item.hours, item.title)):
        if used + task.hours <= available_hours + 1e-9:
            selected.append(task)
            used += task.hours
    return selected


def _improved_knapsack(tasks: list[Task], available_hours: float, slot_minutes: int) -> list[Task]:
    capacity = int(round(available_hours * 60 / slot_minutes))
    weights = [max(1, int(round(task.hours * 60 / slot_minutes))) for task in tasks]

    dp: list[tuple[float, tuple[int, ...]]] = [(0.0, tuple()) for _ in range(capacity + 1)]
    for index, task in enumerate(tasks):
        weight = weights[index]
        if weight > capacity:
            continue
        for current_capacity in range(capacity, weight - 1, -1):
            previous_value, previous_indexes = dp[current_capacity - weight]
            candidate_value = previous_value + task.value
            current_value, current_indexes = dp[current_capacity]
            candidate_indexes = (*previous_indexes, index)
            if (
                candidate_value > current_value
                or (
                    candidate_value == current_value
                    and _total_hours(tasks, candidate_indexes) < _total_hours(tasks, current_indexes)
                )
            ):
                dp[current_capacity] = (candidate_value, candidate_indexes)

    _, selected_indexes = max(
        dp,
        key=lambda item: (item[0], -_total_hours(tasks, item[1])),
    )
    return [tasks[index] for index in selected_indexes]


def _total_hours(tasks: list[Task], indexes: tuple[int, ...]) -> float:
    return sum(tasks[index].hours for index in indexes)


@tool(
    name="plan_optimizer",
    description=(
        "Solve a time or budget allocation task. It compares a simple greedy baseline "
        "with an improved 0/1 knapsack solution and explains which tasks fit into the limit."
    ),
    parameters={
        "type": "object",
        "properties": {
            "available_hours": {
                "type": "number",
                "description": "Total available time budget in hours.",
            },
            "tasks": {
                "type": "array",
                "description": "Candidate tasks with title/name, hours, and value or priority.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "name": {"type": "string"},
                        "hours": {"type": "number"},
                        "value": {"type": "number"},
                        "priority": {"type": "number"},
                    },
                    "required": ["hours"],
                    "additionalProperties": True,
                },
            },
            "slot_minutes": {
                "type": "integer",
                "description": "Optimization granularity in minutes. Default is 30.",
            },
        },
        "required": ["available_hours", "tasks"],
        "additionalProperties": False,
    },
)
def plan_optimizer(arguments: JsonDict) -> JsonDict:
    available_hours = _as_float(arguments.get("available_hours"), field="available_hours")
    if available_hours <= 0:
        raise ValueError("available_hours must be greater than zero")

    slot_minutes = int(arguments.get("slot_minutes") or 30)
    if slot_minutes <= 0 or slot_minutes > 240:
        raise ValueError("slot_minutes must be between 1 and 240")

    tasks = _load_tasks(arguments.get("tasks"))
    baseline = _baseline_greedy(tasks, available_hours)
    improved = _improved_knapsack(tasks, available_hours, slot_minutes)

    baseline_summary = _summarize(baseline, available_hours)
    improved_summary = _summarize(improved, available_hours)
    skipped = [task for task in tasks if task.id not in {selected.id for selected in improved}]

    return {
        "available_hours": available_hours,
        "slot_minutes": slot_minutes,
        "baseline": {
            "method": "greedy by value_per_hour",
            **baseline_summary,
        },
        "improved": {
            "method": "0/1 knapsack dynamic programming",
            **improved_summary,
        },
        "comparison": {
            "value_gain": round(
                improved_summary["total_value"] - baseline_summary["total_value"],
                2,
            ),
            "hours_delta": round(
                improved_summary["used_hours"] - baseline_summary["used_hours"],
                2,
            ),
            "improved_is_better": improved_summary["total_value"] > baseline_summary["total_value"],
        },
        "skipped_tasks": [_serialize_task(task) for task in skipped],
    }
