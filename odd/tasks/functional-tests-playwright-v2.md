# Functional tests Playwright v2
Simplify the functional test set, repair observed failures, execute each module through the public UI, and embed clear screenshot evidence in the existing workbook.

## Specs
1. S1 — "revisa las pruebas funcionales y corrijamos lo que aparece fallido"
2. S2 — "corrijamos el set de pruebas funcionales del excel para que sean pruebas mas sencillas"
3. S3 — "que comprueben que cada modulo funciona bien tanto para el administrador como operador"
4. S4 — "hagamoslas con playright registrando la evidencia en imagenes"
5. S5 — "como responsable pon mi nombre"
6. S6 — "en la prueba y secuencia se mas claro con lo que se va hacer y el resultado esperado"
7. S7 — Responsable confirmado: "Camilo Pieschacón".
8. S8 — Workbook confirmado: `C:\Users\USUARIO\Desktop\Ingenieria de Software\S25 - Evidencia de Aprendizaje 2. Diseño Sistema de Información – Iteración 2\entregables\Plan_Pruebas_Funcionalidad_Autos_Colombia.xlsx`.

## Tasks
- T1 [S1-S3,S6] Reproduce and classify every currently failed or pending functional case against the live Docker application. Route: parent + Playwright. Commit: this feature slice.
- T2 [S1,S3] Repair confirmed application defects required for simple administrator/operator module coverage, with focused automated checks. Route: parent TDD. Commit: this feature slice.
- T3 [S2-S3,S6-S8] Redesign the workbook cases into a simpler role/module matrix with explicit action sequence and observable expected result. Route: parent spreadsheet edit. Commit: external artifact and generator scripts.
- T4 [S3-S5] Execute the simplified cases with Playwright for administrator and operator, capture one clear PNG per case, and embed the images in the workbook. Route: parent Playwright. Commit: evidence artifact.
- T5 [S1-S8] Recalculate and verify workbook formulas, inspect evidence/layout, run application regression checks, and report failures or limits. Route: parent checks. Commit: this feature slice.

## Log
- L1 — listo ahora revisa las pruebas funcionales y corrijamos lo que aparece fallido. por otro lado corrijamos el set de pruebas funcionales del excel para que sean pruebas mas sencillas que comprueben que cada modulo funciona bien tanto para el administrador como operador y hagamoslas con playright registrando la evidencia en imagenes pero como responsable pon mi nombre y en la prueba y secuencia se mas claro con lo que se va hacer y el resultado esperado
- L2 — The existing workbook contains 28 cases and 28 embedded images. Current statuses: five failed cases (`EN-07`, `CO-02`, `OC-01`, `RE-01`, `RE-02`) and one pending integrated regression (`RG-03`).
- L3 — User authorized the external workbook path in S8 and confirmed `Camilo Pieschacón` as the responsible name.
- L4 — Reproduction: `EN-07`/`RG-01` were genuine missing active-entry responsibility; `CO-02` was blocked by a generic frontend validation; `OC-01` lacked visible type totals. `RE-01` and `RE-02` expected unimplemented advanced reports and were removed from the simplified scope instead of expanding the product.
- L5 — Application fixes: `/api/movimientos/activos` now returns `operario_entrada`; Vehículos presentes displays it; Ocupación shows libres/ocupadas/inactivas for motos and automóviles; Corrección surfaces the backend's specific occupied-cell error. Focused backend RED then GREEN passed; Angular build passed; live Docker UI confirmed all three corrections.
- L6 — Workbook redesign: 12 cases `PF-01`–`PF-12`, one per role/module outcome, with numbered steps, explicit expected results, no advanced date/monthly-expiration report expectations, and `Camilo Pieschacón` in every responsible cell.
- L7 — Playwright execution: all 12 cases passed. Evidence `PF-01.png`–`PF-12.png` was captured and embedded. The CAR202 flow assigned A-04, rejected occupied A-01, corrected to A-05, exited with receipt `5NhFDlaMWtKCfhvPtkZGVahicxnlSpr7`, and appeared in closed history with responsible operators and correction.
- L8 — Verification: backend suite 126 passed / 4 skipped; Angular development build passed; Excel COM recalculated 23 formulas with zero errors; plan summary is 12 planned, 12 approved, 0 pending, 0 failed, 100% approval; every case record is `Completo`; 12 images and zero hyperlinks; evidence montage inspected successfully.
