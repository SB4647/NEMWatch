from pathlib import Path

import pytest

from nemwatch.domain.models import Region
from nemwatch.replay.service import ReplayService


@pytest.mark.anyio
async def test_replay_rejects_unknown_source_before_database_access(tmp_path: Path) -> None:
    service = ReplayService(None, None, None, tmp_path)  # type: ignore[arg-type]
    with pytest.raises(FileNotFoundError):
        await service.start("missing.csv", (Region.QLD1,), 100)
