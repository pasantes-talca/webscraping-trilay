import os
from pathlib import Path

from dotenv import load_dotenv

from utils.fechas import (
    formatos_fecha_facturacion,
)


# ==========================================
# PROYECTO
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

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


# ==========================================
# FILTROS
# ==========================================

FECHA_DESDE, FECHA_CARPETA = formatos_fecha_facturacion()
FECHA_HASTA = FECHA_DESDE

CLIENTE = "atomo"


# ==========================================
# SUCURSAL
# ==========================================

SUCURSAL = "MENDOZA"

SUCURSALES = {
    "MENDOZA": "7",
}


# ==========================================
# FACTURAS
# ==========================================

CARPETA_FACTURAS = Path(
    os.getenv(
        "SERVIDOR_RUTA",
        r"\\192.168.10.3\Facturas Jumbo",
    )
)


# ==========================================
# KRIKOS
# ==========================================

KRIKOS_DATA_DIR = Path(
    os.getenv(
        "KRIKOS_DATA_DIR",
        str(BASE_DIR / "data"),
    )
)

KRIKOS_EMAIL = os.getenv("KRIKOS_EMAIL", os.getenv("EMAIL"))
KRIKOS_PASSWORD = os.getenv("KRIKOS_PASSWORD", os.getenv("PASSWORD"))
KRIKOS_URL = os.getenv("KRIKOS_URL", os.getenv("URL"))

SERVIDOR_USUARIO = os.getenv("SERVIDOR_USUARIO")
SERVIDOR_PASSWORD = os.getenv("SERVIDOR_PASSWORD")

CARPETA_DATA = KRIKOS_DATA_DIR
ARCHIVO_ESTADO_SESION = CARPETA_DATA / "estado_sesion.json"
ARCHIVO_MAPEO_SUCURSALES = (
    CARPETA_DATA / "Mapeo_Sucursales_Completo.xlsx"
)

IMPUESTO_BEBIDAS = 0.087
IMPUESTO_LIMA = 0.0417
IMPUESTO_SODA = 0.0

ENVIAR_FACTURA_AUTOMATICAMENTE = True
ESPERA_POST_ENVIO_MS = 1800


# ==========================================
# CORREO DEL RESULTADO
# ==========================================

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USUARIO = os.getenv("SMTP_USUARIO")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_USAR_SSL = os.getenv(
    "SMTP_USAR_SSL",
    "false",
).lower() in {"1", "true", "si", "yes"}

MAIL_DESDE = os.getenv("MAIL_DESDE", SMTP_USUARIO)
MAIL_PARA = [
    direccion.strip()
    for direccion in os.getenv("MAIL_PARA", "").split(",")
    if direccion.strip()
]
