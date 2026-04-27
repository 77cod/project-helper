from __future__ import annotations

import asyncio
import json
from collections import defaultdict


class EventBus:
    def __init__(self) -> None:
        self._channels: dict[str, list[str]] = defaultdict(list)
        self._conditions: dict[str, asyncio.Condition] = defaultdict(asyncio.Condition)

    async def publish(self, channel: str, payload: dict) -> None:
        self._channels[channel].append(json.dumps(payload, ensure_ascii=False))
        condition = self._conditions[channel]
        async with condition:
            condition.notify_all()

    async def stream(self, channel: str):
        index = 0
        while True:
            while index < len(self._channels[channel]):
                message = self._channels[channel][index]
                index += 1
                yield f"data: {message}\n\n"

            condition = self._conditions[channel]
            async with condition:
                await condition.wait()
