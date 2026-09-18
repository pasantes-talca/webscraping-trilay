import ctypes
import os
import time
from pathlib import Path


def cerrar_dialogo_archivo_so():

    try:

        user32 = ctypes.windll.user32

        hwnd = user32.FindWindowW(
            "#32770",
            None,
        )


        if hwnd:

            user32.PostMessageW(
                hwnd,
                0x0010,
                0,
                0,
            )


    except Exception:
        pass


def validar_pdf(
    ruta_pdf,
):

    ruta = Path(
        ruta_pdf
    )


    if not ruta.exists():

        raise FileNotFoundError(
            f"No existe el archivo PDF: {ruta}"
        )


    if not ruta.is_file():

        raise RuntimeError(
            f"La ruta no corresponde a un archivo: {ruta}"
        )


    if ruta.suffix.lower() != ".pdf":

        raise RuntimeError(
            f"El archivo no es un PDF: {ruta.name}"
        )


    if ruta.stat().st_size == 0:

        raise RuntimeError(
            f"El PDF está vacío: {ruta.name}"
        )


    return True


def esperar_archivo_estable(
    ruta_archivo,
    intentos=5,
    espera=1,
):

    ruta = Path(
        ruta_archivo
    )


    if not ruta.exists():

        return False


    tamano_anterior = -1


    for _ in range(
        intentos
    ):

        try:

            tamano_actual = (
                ruta.stat().st_size
            )

        except OSError:

            return False


        if (
            tamano_actual > 0
            and
            tamano_actual
            == tamano_anterior
        ):

            return True


        tamano_anterior = (
            tamano_actual
        )


        time.sleep(
            espera
        )


    return False


def validar_datos_factura(
    datos,
):

    if not datos:

        raise RuntimeError(
            "No se pudieron extraer "
            "los datos de la factura."
        )


    if (
        datos.get(
            "tipo_factura"
        )
        != "General"
    ):

        raise RuntimeError(
            "La factura no es de tipo General."
        )


    if not datos.get(
        "productos"
    ):

        raise RuntimeError(
            "La factura no contiene productos."
        )


    if not datos.get(
        "gln"
    ):

        raise RuntimeError(
            "No se pudo determinar el GLN."
        )


    if not datos.get(
        "sucursal"
    ):

        raise RuntimeError(
            "No se pudo determinar la sucursal."
        )


    return True