import os
import subprocess
import sys
from pathlib import Path

from config import (
    CARPETA_FACTURAS,
    KRIKOS_DATA_DIR,
    KRIKOS_PROYECTO,
)


ARCHIVO_MAPEO_GLN = "Mapeo_Sucursales_Completo.xlsx"


def cargar_facturas_en_krikos(fecha_carpeta):
    """Ejecuta Krikos sobre la misma fecha que proceso Trilay."""

    proyecto = Path(KRIKOS_PROYECTO).resolve()
    programa = proyecto / "main.py"
    extractor = proyecto / "extractor.py"
    carpeta_data = Path(KRIKOS_DATA_DIR).resolve()
    archivo_mapeo = carpeta_data / ARCHIVO_MAPEO_GLN

    if not programa.is_file():
        raise FileNotFoundError(
            "No se encontro el programa de Krikos en "
            f"{programa}. Configura KRIKOS_PROYECTO en .env."
        )

    if not extractor.is_file():
        raise FileNotFoundError(
            "No se encontro el extractor de facturas de Krikos en "
            f"{extractor}. Configura KRIKOS_PROYECTO en .env."
        )

    if not archivo_mapeo.is_file():
        raise FileNotFoundError(
            "No se encontro el Excel de sucursales y GLN en "
            f"{archivo_mapeo}."
        )

    entorno = os.environ.copy()

    # Garantiza que Krikos lea la misma raiz donde Trilay acaba
    # de crear la carpeta DD-MM-YYYY y mover los PDF descargados.
    entorno["SERVIDOR_RUTA"] = str(CARPETA_FACTURAS)
    entorno["KRIKOS_DATA_DIR"] = str(carpeta_data)
    entorno["FECHA_PROCESO"] = fecha_carpeta
    entorno["PYTHONUNBUFFERED"] = "1"

    print(f"Iniciando Krikos desde: {proyecto}")
    print("Iniciando registro y carga de facturas en Krikos...")

    resultado = subprocess.run(
        [sys.executable, str(programa)],
        cwd=str(proyecto),
        env=entorno,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if resultado.stdout:
        print(resultado.stdout, end="")

    if resultado.stderr:
        print(resultado.stderr, end="", file=sys.stderr)

    if resultado.returncode != 0:
        raise RuntimeError(
            "Krikos termino con el codigo de error "
            f"{resultado.returncode}."
        )

    print("Proceso de Krikos finalizado.")
