from copy import copy
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

WORKBOOK = Path(
    r"C:\Users\USUARIO\Desktop\Ingenieria de Software\S25 - Evidencia de Aprendizaje 2. Diseño Sistema de Información – Iteración 2\entregables\Plan_Pruebas_Funcionalidad_Autos_Colombia.xlsx"
)

CASES = [
    ("PF-01", "Administrador · Acceso", "Iniciar sesión como administrador y revisar el menú completo", "Aplicación disponible. Usuario admin activo.", "1. Abrir el inicio de sesión.\n2. Ingresar admin / Admin2026.\n3. Presionar Ingresar.\n4. Revisar el menú lateral.", "Se abre Inicio con el rol Administrador. El menú muestra Operadores, Celdas, Registrar vehículo, Gestionar vehículos y los módulos operativos.", "Crítica"),
    ("PF-02", "Administrador · Operadores", "Consultar la gestión de operadores", "Sesión iniciada como administrador.", "1. Abrir Operadores.\n2. Confirmar que aparece el listado.\n3. Abrir un operador existente.\n4. Volver sin guardar cambios.", "El listado muestra usuario, nombre, rol y estado. La pantalla de gestión del operador abre correctamente.", "Alta"),
    ("PF-03", "Administrador · Celdas", "Consultar el catálogo y la creación de celdas", "Sesión iniciada como administrador.", "1. Abrir Celdas.\n2. Revisar código, categoría y estado.\n3. Abrir Nueva celda.\n4. Volver sin crear registros.", "El catálogo diferencia celdas disponibles, ocupadas e inactivas. El formulario Nueva celda abre con código y categoría.", "Alta"),
    ("PF-04", "Administrador · Vehículos", "Buscar un vehículo desde la gestión administrativa", "Sesión iniciada como administrador. La placa ABC123 existe.", "1. Abrir Gestionar vehículos.\n2. Escribir ABC123.\n3. Presionar Buscar.\n4. Revisar los datos cargados.", "Se muestran placa, tipo, marca, modelo, color, cliente y estado del vehículo sin mensajes de error.", "Alta"),
    ("PF-05", "Operador · Acceso", "Iniciar sesión como operador y comprobar sus permisos", "Usuario operario1 activo. Sesión de administrador cerrada.", "1. Ingresar con operario1 / Operario2026.\n2. Revisar el menú lateral.\n3. Intentar abrir /operadores.", "El operador ve solo módulos operativos. No aparecen Operadores, Celdas ni Gestionar vehículos. La ruta /operadores muestra Acceso denegado.", "Crítica"),
    ("PF-06", "Operador · Registrar vehículo", "Registrar una placa nueva para un cliente existente", "Sesión iniciada como operador. PFT101 no existe. Hay clientes en el selector.", "1. Abrir Registrar vehículo.\n2. Escribir PFT101, CARRO, Renault, Logan y Gris.\n3. Seleccionar el primer cliente.\n4. Presionar Registrar vehículo.", "La aplicación confirma “Vehículo PFT101 registrado correctamente” y no muestra errores.", "Alta"),
    ("PF-07", "Operador · Entrada", "Registrar la entrada de un vehículo autorizado", "CAR202 tiene mensualidad vigente, no está dentro y existe una celda de automóvil libre.", "1. Abrir Entrada.\n2. Escribir CAR202 y consultar.\n3. Revisar marca, modelo y color.\n4. Continuar y confirmar la entrada.", "La entrada queda registrada, se asigna una celda de automóvil y se muestra un comprobante para la salida.", "Crítica"),
    ("PF-08", "Operador · Vehículos presentes", "Consultar el vehículo que acaba de ingresar", "PF-07 aprobado y CAR202 con permanencia abierta.", "1. Abrir Vehículos presentes.\n2. Buscar CAR202.\n3. Revisar celda, hora, responsable y comprobante.", "CAR202 aparece una vez con celda, fecha, Operario Diurno 1 como responsable y el comprobante generado en PF-07.", "Alta"),
    ("PF-09", "Operador · Ocupación", "Revisar la ocupación general y por tipo de vehículo", "PF-07 aprobado y sesión iniciada como operador.", "1. Abrir Ocupación.\n2. Revisar el resumen general.\n3. Revisar Motos y Automóviles.\n4. Ubicar la celda de CAR202.", "Se muestran libres, ocupadas e inactivas por motos y automóviles. La celda de CAR202 aparece ocupada.", "Alta"),
    ("PF-10", "Operador · Corrección de celda", "Validar una celda ocupada y corregir hacia una libre", "CAR202 está dentro. Existe otra celda ocupada y una celda libre compatible.", "1. Abrir Corregir celda para CAR202.\n2. Guardar una celda ocupada.\n3. Comprobar el mensaje.\n4. Guardar una celda libre compatible.", "El primer intento indica que la celda pertenece a otra permanencia. El segundo actualiza la celda y muestra la auditoría.", "Alta"),
    ("PF-11", "Operador · Salida", "Registrar la salida con el comprobante de entrada", "PF-07 aprobado. Conservar el comprobante de CAR202.", "1. Abrir Salida.\n2. Escribir el comprobante y consultar.\n3. Revisar placa y celda.\n4. Confirmar la salida.", "Se confirma la salida, CAR202 deja de aparecer en presentes y su celda final queda libre.", "Crítica"),
    ("PF-12", "Operador · Reportes", "Consultar ocupación e historial después del flujo", "PF-11 aprobado y sesión iniciada como operador.", "1. Abrir Reportes.\n2. Revisar los totales.\n3. Buscar CAR202 en Permanencias cerradas.\n4. Revisar responsables, comprobante y corrección.", "Reportes abre para el operador. CAR202 aparece con responsables, comprobante y la corrección de PF-10.", "Alta"),
]


def apply_style(cell, style):
    cell.font = copy(style["font"])
    cell.fill = copy(style["fill"])
    cell.border = copy(style["border"])
    cell.alignment = copy(style["alignment"])
    cell.number_format = style["number_format"]
    cell.protection = copy(style["protection"])


wb = load_workbook(WORKBOOK)
plan = wb["Plan"]
ws = wb["Casos"]
ws._images = []
if ws.max_row > 17:
    ws.delete_rows(18, ws.max_row - 17)

headers = ["ID", "Rol / módulo", "Prueba y secuencia", "Precondiciones y datos", "Pasos", "Resultado esperado", "Prioridad", "Estado", "Resultado real / justificación", "Evidencia PNG", "Incidencia / bloqueo", "Fecha de ejecución", "Responsable", "Registro de ejecución"]
for column, value in enumerate(headers, 1):
    ws.cell(5, column, value)

styles = {}
for column in range(1, 15):
    source = ws.cell(6, column)
    styles[column] = {name: copy(getattr(source, name)) for name in ("font", "fill", "border", "alignment", "protection")}
    styles[column]["number_format"] = source.number_format

for row, case in enumerate(CASES, 6):
    values = [*case, "Pendiente", "", "Pendiente de ejecución Playwright", "", None, "Camilo Pieschacón"]
    values.append(
        f'=IF(H{row}="Pendiente","Pendiente",IF(AND(H{row}<>"Aprobado",H{row}<>"Fallido",H{row}<>"Bloqueado",H{row}<>"No aplica"),"Revisar estado",IF(OR(I{row}="",M{row}="",NOT(ISNUMBER(L{row}))),"Faltan datos",IF(H{row}="No aplica",IF(K{row}="","Falta justificación","Completo"),IF(OR(H{row}="Fallido",H{row}="Bloqueado"),IF(K{row}="","Falta incidencia","Completo"),IF(J{row}="","Falta evidencia","Completo"))))))'
    )
    for column, value in enumerate(values, 1):
        cell = ws.cell(row, column, value)
        apply_style(cell, styles[column])
    ws.row_dimensions[row].height = 112

ws["A2"] = "Casos simples por rol y módulo. Ejecutar PF-01 a PF-12 y registrar una captura clara por caso."
ws.auto_filter.ref = "A5:N17"
ws.freeze_panes = "A6"
ws.sheet_view.showGridLines = False

ws.data_validations.dataValidation = []
validations = [
    (DataValidation(type="list", formula1="'_Listas'!$A$2:$A$6", allow_blank=False), "H6:H17"),
    (DataValidation(type="list", formula1="'_Listas'!$B$2:$B$5", allow_blank=False), "G6:G17"),
    (DataValidation(type="date", operator="between", formula1="DATE(2025,1,1)", formula2="DATE(2030,12,31)", allow_blank=True), "L6:L17"),
]
for validation, target in validations:
    ws.add_data_validation(validation)
    validation.add(target)

editable_fill = PatternFill("solid", fgColor="FFF2CC")
for row in range(6, 18):
    for column in range(8, 14):
        ws.cell(row, column).fill = copy(editable_fill)

ws.conditional_formatting._cf_rules.clear()
for state, fill, color in (("Aprobado", "C6EFCE", "006100"), ("Fallido", "FFC7CE", "9C0006"), ("Pendiente", "FFF2CC", "7F6000")):
    ws.conditional_formatting.add("H6:H17", FormulaRule(formula=[f'H6="{state}"'], fill=PatternFill("solid", fgColor=fill), font=Font(color=color)))

for cell, formula in {
    "B6": '=COUNTA(Casos!$A$6:$A$17)',
    "B7": '=COUNTIFS(Casos!$H$6:$H$17,"Pendiente")',
    "B8": '=COUNTIFS(Casos!$H$6:$H$17,"Aprobado")',
    "B9": '=COUNTIFS(Casos!$H$6:$H$17,"Fallido")',
    "B10": '=COUNTIFS(Casos!$H$6:$H$17,"Bloqueado")',
    "B11": '=COUNTIFS(Casos!$H$6:$H$17,"No aplica")',
    "B15": '=COUNTIFS(Casos!$N$6:$N$17,"Falt*")+COUNTIFS(Casos!$N$6:$N$17,"Revisar estado")',
}.items():
    plan[cell] = formula

plan["E7"] = "Camilo Pieschacón"
plan["E8"] = "Rama test/i2-t26-security-concurrency-regression"
plan["E9"] = "Docker Compose local: frontend 4200, backend 8080, PostgreSQL 16"
plan["E10"] = datetime.now().date()
plan["E12"] = datetime.now().date()
plan["E15"] = "Amarillo: campos de ejecución. Cada caso tiene una secuencia corta y un resultado observable. La evidencia PNG se incrusta en la columna J."
plan["B19"] = "Comprobar con casos sencillos que cada módulo visible funciona según el rol Administrador u Operador."
plan["B20"] = "Administrador: acceso, operadores, celdas y gestión de vehículos. Operador: acceso, registro de vehículo, entrada, presentes, ocupación, corrección, salida y reportes."
plan["B21"] = "No se evalúan pagos, mantenimiento de clientes ni reportes no implementados como mensualidades vencidas o filtros avanzados por fecha."
plan["B25"] = "Un caso por módulo. PF-06 a PF-12 forman un flujo operativo corto con CAR202 y su comprobante."
plan["B27"] = "Una captura PNG por caso, tomada después de observar el resultado esperado e incrustada en Evidencia PNG."
plan["B32"] = "Plan simplificado y listo para ejecución Playwright."

for sheet in (plan, ws):
    for row in sheet.iter_rows():
        for cell in row:
            if cell.value is None:
                continue
            original = cell.font
            color = original.color
            cell.font = Font(name="Arial", size=original.sz or 10, bold=original.bold, italic=original.italic, color=color)
            alignment = cell.alignment
            cell.alignment = Alignment(horizontal=alignment.horizontal, vertical=alignment.vertical or "top", wrap_text=True)

wb.save(WORKBOOK)
print(f"Plan actualizado: {len(CASES)} casos")
