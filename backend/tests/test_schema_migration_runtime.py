from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest


ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_SCHEMA_MIGRATION_DOCKER") != "1",
    reason="Set RUN_SCHEMA_MIGRATION_DOCKER=1 to run the isolated PostgreSQL migration test.",
)


def run(*args: str, timeout: int = 120, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=check,
    )


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def request(
    base_url: str,
    method: str,
    path: str,
    data: dict | None = None,
    token: str | None = None,
) -> tuple[int, dict | list | None]:
    body = None if data is None else json.dumps(data).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    outbound = Request(base_url + path, data=body, headers=headers, method=method)
    try:
        with urlopen(outbound, timeout=10) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except HTTPError as error:
        raw = error.read()
        return error.code, json.loads(raw) if raw else None


def wait_for_database(container: str) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        result = run(
            "docker", "exec", container,
            "pg_isready", "-U", "autos_colombia", "-d", "autos_colombia",
            check=False,
            timeout=5,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise AssertionError(run("docker", "logs", container, check=False).stdout)


def wait_for_backend(base_url: str, container: str) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            status, body = request(base_url, "GET", "/api/health")
            if status == 200 and body == {"status": "ok", "service": "backend"}:
                return
        except Exception:
            pass
        time.sleep(1)
    logs = run("docker", "logs", container, check=False).stdout
    raise AssertionError(f"backend did not become healthy\n{logs}")


def sql(container: str, statement: str) -> list[str]:
    result = run(
        "docker", "exec", container,
        "psql", "-U", "autos_colombia", "-d", "autos_colombia",
        "-At", "-c", statement,
        timeout=30,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_legacy_postgres_volume_is_upgraded_before_http_start() -> None:
    suffix = uuid4().hex[:10]
    network = f"autos-migration-{suffix}"
    database = f"autos-migration-db-{suffix}"
    backend = f"autos-migration-api-{suffix}"
    image = f"autos-migration-backend:{suffix}"
    port = available_port()
    base_url = f"http://127.0.0.1:{port}"
    schema = (ROOT / "backend" / "scripts" / "schema.sql").resolve()
    seed = (ROOT / "backend" / "scripts" / "seed.sql").resolve()

    run("docker", "network", "create", network)
    try:
        run(
            "docker", "run", "-d", "--rm", "--name", database,
            "--network", network,
            "-e", "POSTGRES_DB=autos_colombia",
            "-e", "POSTGRES_USER=autos_colombia",
            "-e", "POSTGRES_PASSWORD=autos_colombia_test",
            "-v", f"{schema}:/docker-entrypoint-initdb.d/01-schema.sql:ro",
            "-v", f"{seed}:/docker-entrypoint-initdb.d/02-seed.sql:ro",
            "postgres:16-alpine",
        )
        wait_for_database(database)
        assert sql(database, "SELECT count(*) FROM vehicles WHERE license_plate='ABC123';") == ["1"]

        sql(database, "DROP TABLE vehicle_audits; ALTER TABLE vehicles DROP COLUMN active;")
        assert sql(
            database,
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_name='vehicles' AND column_name='active';",
        ) == ["0"]

        run("docker", "build", "-t", image, "backend", timeout=180)
        run(
            "docker", "run", "-d", "--rm", "--name", backend,
            "--network", network,
            "-p", f"127.0.0.1:{port}:8000",
            "-e", f"DB_HOST={database}",
            "-e", "DB_PORT=5432",
            "-e", "POSTGRES_DB=autos_colombia",
            "-e", "POSTGRES_USER=autos_colombia",
            "-e", "POSTGRES_PASSWORD=autos_colombia_test",
            "-e", "AUTH_SECRET=isolated-schema-migration-test-secret",
            image,
        )
        wait_for_backend(base_url, backend)

        status, login = request(
            base_url,
            "POST",
            "/api/auth/login",
            {"username": "operario1", "password": "Operario2026"},
        )
        assert status == 200 and isinstance(login, dict)
        token = str(login["access_token"])

        status, clients = request(base_url, "GET", "/api/clientes", token=token)
        assert status == 200 and isinstance(clients, list) and clients
        status, created = request(
            base_url,
            "POST",
            "/api/vehiculos",
            {
                "placa": "MIG001",
                "tipo": "CARRO",
                "marca": "Renault",
                "modelo": "Logan",
                "color": "Gris",
                "cliente_id": clients[0]["id"],
            },
            token,
        )
        assert status == 201 and isinstance(created, dict) and created["activo"] is True

        status, lookup = request(base_url, "GET", "/api/vehiculos/ABC123", token=token)
        assert status == 200 and isinstance(lookup, dict)
        assert lookup["placa"] == "ABC123" and lookup["authorized"] is True

        assert sql(
            database,
            "SELECT is_nullable || '|' || column_default "
            "FROM information_schema.columns "
            "WHERE table_name='vehicles' AND column_name='active';",
        ) == ["NO|true"]
        assert sql(database, "SELECT to_regclass('public.vehicle_audits');") == ["vehicle_audits"]
        assert sql(
            database,
            "SELECT va.action || '|' || ua.username FROM vehicle_audits va "
            "JOIN user_accounts ua ON ua.id=va.account_id "
            "JOIN vehicles v ON v.id=va.vehicle_id WHERE v.license_plate='MIG001';",
        ) == ["CREATE|operario1"]

        run("docker", "restart", backend, timeout=30)
        wait_for_backend(base_url, backend)
        status, login = request(
            base_url,
            "POST",
            "/api/auth/login",
            {"username": "operario1", "password": "Operario2026"},
        )
        assert status == 200 and isinstance(login, dict)
        status, lookup = request(
            base_url,
            "GET",
            "/api/vehiculos/ABC123",
            token=str(login["access_token"]),
        )
        assert status == 200 and isinstance(lookup, dict) and lookup["authorized"] is True
    finally:
        run("docker", "stop", backend, database, check=False, timeout=30)
        run("docker", "network", "rm", network, check=False, timeout=30)
        run("docker", "image", "rm", image, check=False, timeout=30)
