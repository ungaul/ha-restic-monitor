from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, tzinfo
import os
from pathlib import Path

ERR_NONE = "none"
ERR_NOT_FOUND = "not_found"
ERR_PERMISSION = "permission_denied"
ERR_IO = "io_error"

@dataclass
class RepoStatus:
    available: bool
    snapshot_times: list[datetime] = field(default_factory=list)
    size: int | None = None
    error_code: str = ERR_NONE
    error: str | None = None

    @property
    def snapshot_count(self) -> int:
        return len(self.snapshot_times)

    @property
    def last_snapshot(self) -> datetime | None:
        return max(self.snapshot_times) if self.snapshot_times else None


def is_repository(path: str | os.PathLike[str]) -> bool:
    p = Path(path)
    try:
        return (p / "config").is_file() and (p / "snapshots").is_dir()
    except OSError:
        return False


def discover(root: str | os.PathLike[str]) -> dict[str, str]:
    root = os.path.realpath(root)
    if is_repository(root):
        return {os.path.basename(root) or "repository": root}
    found: dict[str, str] = {}
    try:
        with os.scandir(root) as it:
            for entry in sorted(it, key=lambda e: e.name):
                if entry.name.startswith(".") or not entry.is_dir():
                    continue
                if is_repository(entry.path):
                    found[entry.name] = entry.path
    except OSError:
        return {}
    return found


def compute_size(path: str | os.PathLike[str]) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.lstat(os.path.join(root, name)).st_size
            except OSError:
                continue
    return total


def _not_readable(path: str | os.PathLike[str]) -> RepoStatus:
    p = Path(path)
    try:
        exists = p.exists()
    except PermissionError:
        return RepoStatus(False, error_code=ERR_PERMISSION, error="permission denied")
    except OSError as err:
        return RepoStatus(False, error_code=ERR_IO, error=str(err))
    if not exists:
        return RepoStatus(False, error_code=ERR_NOT_FOUND, error="path not found (disk not mounted?)")
    return RepoStatus(False, error_code=ERR_NOT_FOUND, error="not a restic repository")


def read_metadata(path: str | os.PathLike[str], size: int | None = None) -> RepoStatus:
    if not is_repository(path):
        return _not_readable(path)
    times: list[datetime] = []
    try:
        with os.scandir(Path(path) / "snapshots") as it:
            for entry in it:
                if entry.is_file():
                    times.append(datetime.fromtimestamp(entry.stat().st_mtime, UTC))
    except PermissionError:
        return RepoStatus(False, error_code=ERR_PERMISSION, error="permission denied")
    except OSError as err:
        return RepoStatus(False, error_code=ERR_IO, error=str(err))
    return RepoStatus(True, snapshot_times=sorted(times), size=size)


def has_snapshot_on(last: datetime | None, day: date, tz: tzinfo | None = None) -> bool:
    return last is not None and last.astimezone(tz).date() == day
