from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.drawing.image import Image

ROOT = Path(__file__).resolve().parent
WORKBOOK = Path(
    r"C:\Users\USUARIO\Desktop\Ingenieria de Software\S25 - Evidencia de Aprendizaje 2. Diseño Sistema de Información – Iteración 2\entregables\Plan_Pruebas_Funcionalidad_Autos_Colombia.xlsx"
)
DATE = datetime.now().date()
RESULTS = {
    "PF-01": "El administrador inició sesión y el menú mostró los módulos administrativos y operativos.",
    "PF-02": "Operadores mostró 3 cuentas activas y abrió la gestión de operario1 sin errores.",
    "PF-03": "Celdas mostró la capacidad de 80 celdas y abrió el formulario Crear celda.",
    "PF-04": "Gestionar vehículos cargó correctamente la información de ABC123.",
    "PF-05": "El operador vio solo opciones operativas y /operadores redirigió a Acceso denegado.",
    "PF-06": "PFT101 se registró correctamente para un cliente existente.",
    "PF-07": "CAR202 ingresó en A-04 y recibió el comprobante 5NhFDlaMWtKCfhvPtkZGVahicxnlSpr7.",
    "PF-08": "Vehículos presentes mostró CAR202 con A-04, Operario Diurno 1 y su comprobante.",
    "PF-09": "Ocupación mostró libres, ocupadas e inactivas por tipo; CAR202 figuró en A-04.",
    "PF-10": "A-01 fue rechazada por estar ocupada y CAR202 se corrigió de A-04 a A-05 con auditoría.",
    "PF-11": "La salida de CAR202 se confirmó con el comprobante y A-05 quedó liberada.",
    "PF-12": "Reportes mostró CAR202 cerrado, responsables de entrada/salida, comprobante y corrección A-04 → A-05.",
}

wb = load_workbook(WORKBOOK)
ws = wb["Casos"]
ws._images = []

for row in range(6, 18):
    case_id = ws.cell(row, 1).value
    image_path = ROOT / f"{case_id}.png"
    if case_id not in RESULTS or not image_path.exists():
        raise FileNotFoundError(f"Falta resultado o evidencia para {case_id}")
    ws.cell(row, 8, "Aprobado")
    ws.cell(row, 9, RESULTS[case_id])
    ws.cell(row, 10, f"Evidencia incrustada: {case_id}.png")
    ws.cell(row, 11, "No aplica")
    ws.cell(row, 12, DATE)
    ws.cell(row, 13, "Camilo Pieschacón")
    ws.row_dimensions[row].height = 165

    image = Image(image_path)
    ratio = min(340 / image.width, 190 / image.height)
    image.width = int(image.width * ratio)
    image.height = int(image.height * ratio)
    image.anchor = f"J{row}"
    ws.add_image(image)

ws.column_dimensions["J"].width = 50
wb["Plan"]["E7"] = "Camilo Pieschacón"
wb["Plan"]["E12"] = DATE
wb["Plan"]["B32"] = "Ejecución Playwright completada: 12 casos aprobados con evidencia PNG incrustada."
wb.save(WORKBOOK)
print(f"Resultados e imágenes incrustados: {len(ws._images)}")
