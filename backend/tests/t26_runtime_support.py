from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]


class T26Runtime:
    def __init__(self, project: str = "autos_t26_pytest") -> None:
        self.project = project
        self.backend_port = 18082
        self.frontend_port = 14202
        self.base_url = f"http://127.0.0.1:{self.backend_port}"
        self.env = os.environ.copy()
        self.env.update(
            AUTH_SECRET="t26-runtime-verification-secret-2026",
            BACKEND_PORT=str(self.backend_port),
            FRONTEND_PORT=str(self.frontend_port),
        )

    def compose(self, *args: str, timeout: int = 240) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["docker", "compose", "-p", self.project, *args],
            cwd=ROOT,
            env=self.env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=True,
        )

    def start(self) -> None:
        self.stop()
        self.compose("up", "-d", "--build")
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            try:
                self.request("GET", "/api/health")
                with urlopen(f"http://127.0.0.1:{self.frontend_port}/", timeout=2):
                    return
            except Exception:
                time.sleep(1)
        raise AssertionError(self.compose("ps").stdout)

    def stop(self) -> None:
        subprocess.run(
            ["docker", "compose", "-p", self.project, "down", "-v", "--remove-orphans"],
            cwd=ROOT,
            env=self.env,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )

    def request_result(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        token: str | None = None,
    ) -> tuple[int, dict | list | None]:
        body = None if data is None else json.dumps(data).encode()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=15) as response:
                status = response.status
                raw = response.read()
        except HTTPError as error:
            status = error.code
            raw = error.read()
        return status, json.loads(raw) if raw else None

    def request(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        token: str | None = None,
        expected: int = 200,
    ) -> dict | list | None:
        status, response = self.request_result(method, path, data, token)
        assert status == expected, f"{method} {path}: expected {expected}, got {status}: {response}"
        return response

    def login(self, username: str, password: str = "Operario2026") -> str:
        response = self.request(
            "POST",
            "/api/auth/login",
            {"username": username, "password": password},
        )
        assert isinstance(response, dict)
        return str(response["access_token"])

    def sql(self, statement: str) -> list[list[str]]:
        result = self.compose(
            "exec",
            "-T",
            "db",
            "psql",
            "-U",
            "autos_colombia",
            "-d",
            "autos_colombia",
            "-At",
            "-F",
            "|",
            "-c",
            statement,
            timeout=30,
        )
        return [line.split("|") for line in result.stdout.splitlines() if line]

    def reset_operational_state(self) -> None:
        self.sql(
            "BEGIN;"
            "DELETE FROM cell_corrections;"
            "DELETE FROM receipts;"
            "DELETE FROM parking_stays;"
            "UPDATE parking_spots SET active = TRUE;"
            "COMMIT;"
        )

    def prepare_vehicles(self, *plates: str, vehicle_type: str = "CARRO") -> None:
        values = ",".join(
            f"('{plate}', '{vehicle_type}'::vehicle_type, 'T26', 'Concurrente', 'Azul')"
            for plate in plates
        )
        quoted = ",".join(f"'{plate}'" for plate in plates)
        self.sql(
            "BEGIN;"
            f"DELETE FROM receipts WHERE parking_stay_id IN (SELECT id FROM parking_stays WHERE vehicle_id IN (SELECT id FROM vehicles WHERE license_plate IN ({quoted})));"
            f"DELETE FROM cell_corrections WHERE parking_stay_id IN (SELECT id FROM parking_stays WHERE vehicle_id IN (SELECT id FROM vehicles WHERE license_plate IN ({quoted})));"
            f"DELETE FROM parking_stays WHERE vehicle_id IN (SELECT id FROM vehicles WHERE license_plate IN ({quoted}));"
            f"DELETE FROM memberships WHERE vehicle_id IN (SELECT id FROM vehicles WHERE license_plate IN ({quoted}));"
            f"DELETE FROM vehicles WHERE license_plate IN ({quoted});"
            f"INSERT INTO vehicles (license_plate, type, brand, model, color, client_id) SELECT v.plate, v.kind, v.brand, v.model, v.color, c.id FROM (VALUES {values}) AS v(plate, kind, brand, model, color) CROSS JOIN LATERAL (SELECT id FROM clients ORDER BY id LIMIT 1) c;"
            f"INSERT INTO memberships (vehicle_id, starts_at, expires_at) SELECT id, NOW() - INTERVAL '1 day', NOW() + INTERVAL '1 day' FROM vehicles WHERE license_plate IN ({quoted});"
            "COMMIT;"
        )
