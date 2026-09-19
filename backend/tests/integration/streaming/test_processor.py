from dataclasses import dataclass

import pytest

from nemwatch.processing.service import ProcessorService


@dataclass
class InvalidMessage:
    topic: str = "nem.dispatch.observed.v1"
    partition: int = 0
    offset: int = 8
    value: bytes = b"not-json"


@pytest.mark.anyio
async def test_invalid_event_is_dead_lettered_before_offset_commit() -> None:
    calls: list[str] = []

    class Producer:
        async def publish_dead_letter(self, **_values):
            calls.append("dead-letter")

    class Consumer:
        async def commit(self, _offsets):
            calls.append("commit")

    service = ProcessorService(Consumer(), Producer(), None)  # type: ignore[arg-type]
    await service.process_message(InvalidMessage())
    assert calls == ["dead-letter", "commit"]
