from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from t26_runtime_support import T26Runtime

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_T26_DOCKER") != "1",
    reason="Set RUN_T26_DOCKER=1 to run isolated Docker/PostgreSQL T26 tests.",
)


@pytest.fixture(scope="module")
def runtime():
    instance = T26Runtime()
    try:
        instance.start()
        yield instance
    finally:
        instance.stop()


def concurrent_entries(runtime: T26Runtime, attempts: list[tuple[str, str]]):
    barrier = Barrier(len(attempts))
    started_at = time.monotonic()

    def enter(plate: str, token: str):
        barrier.wait(timeout=10)
        status, body = runtime.request_result("POST", "/api/entradas", {"placa": plate}, token)
        return status, body, time.monotonic() - started_at

    with ThreadPoolExecutor(max_workers=len(attempts)) as executor:
        futures = [executor.submit(enter, plate, token) for plate, token in attempts]
        results = [future.result(timeout=30) for future in futures]
    return results, time.monotonic() - started_at


def test_two_operators_enter_simultaneously_with_distinct_cells_and_actors(runtime: T26Runtime):
    runtime.reset_operational_state()
    runtime.prepare_vehicles("T26A01", "T26A02")
    op1 = runtime.login("operario1")
    op2 = runtime.login("operario2")
    runtime.install_entry_delay("T26A")

    results, elapsed = concurrent_entries(runtime, [("T26A01", op1), ("T26A02", op2)])

    assert sorted(status for status, _, _ in results) == [201, 201]
    assert 1.8 <= elapsed < 3.5, f"expected overlapping two-second transactions, got {elapsed:.2f}s"
    bodies = [body for _, body, _ in results]
    assert all(isinstance(body, dict) for body in bodies)
    assert len({body["celda"] for body in bodies}) == 2
    assert len({body["comprobante"] for body in bodies}) == 2

    rows = runtime.sql(
        "SELECT v.license_plate,p.code,ua.username,r.code,r.used_at IS NULL "
        "FROM parking_stays s JOIN vehicles v ON v.id=s.vehicle_id "
        "JOIN parking_spots p ON p.id=s.parking_spot_id "
        "JOIN user_accounts ua ON ua.operator_id=s.entry_operator_id "
        "JOIN receipts r ON r.parking_stay_id=s.id "
        "WHERE v.license_plate IN ('T26A01','T26A02') ORDER BY v.license_plate;"
    )
    assert len(rows) == 2
    persisted = {row[0]: row[1:] for row in rows}
    expected = {
        "T26A01": ("operario1", bodies[0]),
        "T26A02": ("operario2", bodies[1]),
    }
    for plate, (username, response) in expected.items():
        assert persisted[plate] == [response["celda"], username, response["comprobante"], "t"]


def test_last_compatible_cell_allows_one_entry_without_partial_state(runtime: T26Runtime):
    runtime.reset_operational_state()
    runtime.prepare_vehicles("T26C01", "T26C02")
    runtime.sql("UPDATE parking_spots SET active = (code = 'A-70') WHERE category = 'AUTOMOVIL';")
    op1 = runtime.login("operario1")
    op2 = runtime.login("operario2")
    runtime.install_entry_delay("T26C")

    results, _ = concurrent_entries(runtime, [("T26C01", op1), ("T26C02", op2)])

    assert sorted(status for status, _, _ in results) == [201, 409]
    rejected = next(body for status, body, _ in results if status == 409)
    rejected_at = next(finished for status, _, finished in results if status == 409)
    accepted_at = next(finished for status, _, finished in results if status == 201)
    assert rejected_at + 1 < accepted_at, "rejection must occur while the accepted transaction still holds the cell lock"
    assert isinstance(rejected, dict)
    assert rejected["code"] == "NO_COMPATIBLE_SPACE"
    assert runtime.sql(
        "SELECT count(*),count(r.id),count(*) FILTER (WHERE s.exited_at IS NULL) "
        "FROM parking_stays s LEFT JOIN receipts r ON r.parking_stay_id=s.id "
        "JOIN vehicles v ON v.id=s.vehicle_id WHERE v.license_plate IN ('T26C01','T26C02');"
    ) == [["1", "1", "1"]]
    assert runtime.sql(
        "SELECT count(DISTINCT parking_spot_id) FROM parking_stays s JOIN vehicles v ON v.id=s.vehicle_id "
        "WHERE v.license_plate IN ('T26C01','T26C02') AND s.exited_at IS NULL;"
    ) == [["1"]]


def test_permissions_audit_session_invalidation_and_iteration1_regression(runtime: T26Runtime):
    runtime.reset_operational_state()
    runtime.prepare_vehicles("T26R01")
    admin = runtime.login("admin", "Admin2026")
    op1 = runtime.login("operario1")
    op2 = runtime.login("operario2")

    before = runtime.state_fingerprint()
    denied = runtime.request("POST", "/api/celdas", {"codigo": "T26-DENY", "categoria": "AUTOMOVIL"}, op1, 403)
    assert denied["code"] == "FORBIDDEN"
    assert runtime.state_fingerprint() == before

    clients = runtime.request("GET", "/api/clientes", token=op1)
    client_id = clients[0]["id"]
    created = runtime.request(
        "POST",
        "/api/vehiculos",
        {"placa": "T26V01", "tipo": "MOTO", "marca": "T26", "modelo": "Audit", "color": "Negro", "cliente_id": client_id},
        op1,
        201,
    )
    assert created["activo"] is True
    assert runtime.sql(
        "SELECT ua.username,va.action FROM vehicle_audits va JOIN user_accounts ua ON ua.id=va.account_id "
        "JOIN vehicles v ON v.id=va.vehicle_id WHERE v.license_plate='T26V01' ORDER BY va.id DESC LIMIT 1;"
    ) == [["operario1", "CREATE"]]

    entry = runtime.request("POST", "/api/entradas", {"placa": "T26R01"}, op1, 201)
    cells = runtime.request("GET", "/api/celdas", token=op2)
    target = next(cell for cell in cells if cell["categoria"] == "AUTOMOVIL" and cell["estado"] == "disponible" and cell["codigo"] != entry["celda"])
    correction = runtime.request("PATCH", f"/api/movimientos/{entry['permanencia_id']}/celda", {"celda": target["codigo"]}, op2)
    assert correction["celda_nueva"] == target["codigo"]
    report = runtime.request("GET", "/api/reportes/ocupacion", token=op1)
    assert report["vehiculos_presentes"] == 1
    preview = runtime.request("GET", f"/api/salidas/comprobantes/{entry['comprobante']}", token=op1)
    assert preview["placa"] == "T26R01"
    runtime.request("POST", "/api/salidas", {"comprobante": entry["comprobante"]}, op1)

    audit = runtime.sql(
        "SELECT entry_account.username,correction_account.username,exit_account.username,r.used_at IS NOT NULL,s.exited_at IS NOT NULL "
        "FROM parking_stays s JOIN vehicles v ON v.id=s.vehicle_id JOIN receipts r ON r.parking_stay_id=s.id "
        "JOIN user_accounts entry_account ON entry_account.operator_id=s.entry_operator_id "
        "JOIN user_accounts exit_account ON exit_account.operator_id=s.exit_operator_id "
        "JOIN cell_corrections c ON c.parking_stay_id=s.id "
        "JOIN user_accounts correction_account ON correction_account.operator_id=c.operator_id "
        "WHERE v.license_plate='T26R01';"
    )
    assert audit == [["operario1", "operario2", "operario1", "t", "t"]]
    assert runtime.sql(
        "SELECT count(*) FROM parking_stays s JOIN vehicles v ON v.id=s.vehicle_id "
        "WHERE v.license_plate='T26R01' AND s.exited_at IS NULL;"
    ) == [["0"]]

    op2_account = runtime.request("GET", "/api/auth/me", token=op2)
    runtime.request("PATCH", f"/api/operadores/{op2_account['id']}/estado", {"estado": "ANULADA"}, admin)
    snapshot = runtime.state_fingerprint()
    invalid = runtime.request("GET", "/api/movimientos/activos", token=op2, expected=401)
    assert invalid["code"] == "INVALID_SESSION"
    assert runtime.state_fingerprint() == snapshot
    runtime.request("PATCH", f"/api/operadores/{op2_account['id']}/estado", {"estado": "ACTIVA"}, admin)
