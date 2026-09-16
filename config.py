from pathlib import Path

from utils.fechas import fecha_actual


# ==========================================
# PROYECTO
# ==========================================

BASE_DIR = Path(__file__).resolve().parent


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

FECHA_DESDE = fecha_actual()
FECHA_HASTA = fecha_actual()

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
    r"\\192.168.10.3\Facturas Jumbo"
)