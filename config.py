from pathlib import Path
import os

from dotenv import load_dotenv

from utils.fechas import fecha_actual


# ==========================================
# PROYECTO
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = (
    BASE_DIR
    / "data"
)


load_dotenv(
    BASE_DIR / ".env"
)


# ==========================================
# TRILAY
# ==========================================

TRILAY_URL = (
    "http://sistemas.talca.net/trilay/"
)

EDGE_PATH = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
)

IEDRIVER_PATH = (
    BASE_DIR
    / "drivers"
    / "IEDriverServer.exe"
)

LOG_PATH = (
    BASE_DIR
    / "iedriver.log"
)


TRILAY_USUARIO = os.getenv(
    "TRILAY_USUARIO"
)

TRILAY_PASSWORD = os.getenv(
    "TRILAY_PASSWORD"
)


# ==========================================
# FILTROS TRILAY
# ==========================================

FECHA_DESDE = fecha_actual()

FECHA_HASTA = fecha_actual()

CLIENTE = "atomo"


SUCURSAL = "MENDOZA"


SUCURSALES = {
    "MENDOZA": "7",
}


# ==========================================
# SERVIDOR DE FACTURAS
# ==========================================

CARPETA_FACTURAS = Path(
    os.getenv(
        "SERVIDOR_RUTA",
        r"\\192.168.10.3\Facturas Jumbo"
    )
)


SERVIDOR_USUARIO = os.getenv(
    "SERVIDOR_USUARIO"
)

SERVIDOR_PASSWORD = os.getenv(
    "SERVIDOR_PASSWORD"
)


# ==========================================
# KRIKOS
# ==========================================

KRIKOS_EMAIL = os.getenv(
    "KRIKOS_EMAIL"
)

KRIKOS_PASSWORD = os.getenv(
    "KRIKOS_PASSWORD"
)

KRIKOS_URL = os.getenv(
    "KRIKOS_URL"
)


# ==========================================
# ARCHIVOS DE KRIKOS
# ==========================================

ARCHIVO_MAPEO_SUCURSALES = (
    DATA_DIR
    / "Mapeo_Sucursales_Completo.xlsx"
)


CARPETA_DATA = (
    DATA_DIR
)


ARCHIVO_ESTADO_SESION = (
    DATA_DIR
    / "estado_sesion.json"
)


# ==========================================
# CARPETAS DE PROCESO KRIKOS
# ==========================================

CARPETA_PENDIENTES = (
    BASE_DIR
    / "facturas_pendientes"
)

CARPETA_PROCESADAS = (
    BASE_DIR
    / "facturas_procesadas"
)

CARPETA_ERROR = (
    BASE_DIR
    / "facturas_error"
)

CARPETA_CAMBIO = (
    BASE_DIR
    / "facturas_cambio"
)


# ==========================================
# IMPUESTOS
# ==========================================

IMPUESTO_BEBIDAS = 0.087

IMPUESTO_LIMA = 0.0417

IMPUESTO_SODA = 0.0


# ==========================================
# ENVÍO AUTOMÁTICO KRIKOS
# ==========================================

ENVIAR_FACTURA_AUTOMATICAMENTE = True

ESPERA_POST_ENVIO_MS = 1800