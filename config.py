import os
from pathlib import Path

from dotenv import load_dotenv

from utils.fechas import (
    formatos_dia_anterior,
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

FECHA_DESDE, FECHA_CARPETA = formatos_dia_anterior()
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

# Se puede cambiar sin tocar el codigo agregando
# KRIKOS_PROYECTO=<ruta> al archivo .env.
KRIKOS_PROYECTO = Path(
    os.getenv(
        "KRIKOS_PROYECTO",
        str(BASE_DIR.parent / "webscrapping"),
    )
)

KRIKOS_DATA_DIR = Path(
    os.getenv(
        "KRIKOS_DATA_DIR",
        str(BASE_DIR / "data"),
    )
)


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
