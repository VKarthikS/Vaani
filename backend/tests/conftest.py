"""Shared fixtures.

DB tests (marker `db`) need Postgres. They use, in order:
1. VAANI_TEST_DB_URL if set (a database the tests may WIPE — never your dev database), else
2. a throwaway Postgres cluster started from local `initdb`/`pg_ctl` binaries, else
3. they are skipped.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from backend.catalog.loader import load_catalog
from backend.catalog.models import Catalog

PG_BIN_CANDIDATES = [
    "/opt/homebrew/opt/postgresql@17/bin",
    "/opt/homebrew/opt/postgresql@16/bin",
    "/opt/homebrew/opt/postgresql@15/bin",
    "/usr/local/opt/postgresql@15/bin",
    "/usr/lib/postgresql/16/bin",
    "/usr/lib/postgresql/15/bin",
]


@pytest.fixture(scope="session")
def catalog() -> Catalog:
    return load_catalog()


def _pg_bin() -> Path | None:
    found = shutil.which("initdb")
    if found:
        return Path(found).parent
    for c in PG_BIN_CANDIDATES:
        if (Path(c) / "initdb").exists():
            return Path(c)
    return None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture(scope="session")
def pg_url() -> Iterator[str]:
    url = os.environ.get("VAANI_TEST_DB_URL")
    if url:
        yield url
        return
    bin_dir = _pg_bin()
    if bin_dir is None:
        pytest.skip("no Postgres available (set VAANI_TEST_DB_URL or install postgresql)")
    tmp = Path(tempfile.mkdtemp(prefix="vaani-pg-"))
    data, port = tmp / "data", _free_port()
    # macOS: postgres refuses to start without a valid locale in the environment.
    env = {**os.environ, "LC_ALL": "C", "LANG": "C"}

    def run(*cmd: object) -> None:
        r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, env=env)
        if r.returncode != 0:
            log = (tmp / "pg.log").read_text() if (tmp / "pg.log").exists() else ""
            raise RuntimeError(f"{cmd[0]} failed:\n{r.stdout}\n{r.stderr}\n{log[-2000:]}")

    run(bin_dir / "initdb", "-D", data, "-U", "postgres", "-A", "trust", "--no-sync", "--locale=C", "--encoding=UTF8")
    run(
        bin_dir / "pg_ctl",
        "-D",
        data,
        "-l",
        tmp / "pg.log",
        "-w",
        "-o",
        f"-p {port} -k {tmp} -c listen_addresses=127.0.0.1 -c fsync=off -c timezone=UTC",
        "start",
    )
    try:
        yield f"postgresql://postgres@127.0.0.1:{port}/postgres"
    finally:
        subprocess.run(
            [str(bin_dir / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True, env=env
        )
        shutil.rmtree(tmp, ignore_errors=True)
