from __future__ import annotations

import datetime as dt

from agent.tool_api import JsonDict, tool


@tool(
    name="get_current_time",
    description="Get the current local date and time of the CLI process.",
    parameters={"type": "object", "properties": {}, "additionalProperties": False},
)
def get_current_time(_: JsonDict) -> JsonDict:
    now = dt.datetime.now().astimezone()
    return {
        "iso": now.isoformat(),
        "timezone": str(now.tzinfo),
    }

