import time
import shutil
from datetime import datetime
from pathlib import Path

from config import CARPETA_FACTURAS


def registrar_pdfs_existentes():

    if not CARPETA_FACTURAS.exists():

        raise Exception(
            f"No se puede acceder a la carpeta "
            f"{CARPETA_FACTURAS}"
        )

    pdf_anteriores = {}

    for archivo in CARPETA_FACTURAS.glob("*.pdf"):

        try:

            pdf_anteriores[
                archivo.name
            ] = archivo.stat().st_mtime_ns

        except Exception:
            pass

    return pdf_anteriores


def organizar_pdfs_generados(
    pdf_anteriores,
    cantidad_esperada,
):

    # ==========================================
    # CREAR CARPETA DEL DÍA
    # ==========================================

    nombre_carpeta = (
        datetime.now().strftime(
            "%d-%m-%Y"
        )
    )

    carpeta_destino = (
        CARPETA_FACTURAS
        / nombre_carpeta
    )

    carpeta_destino.mkdir(
        parents=True,
        exist_ok=True,
    )


    # ==========================================
    # ESPERAR PDF NUEVOS
    # ==========================================

    limite = time.time() + 60

    pdf_generados = []


    while time.time() < limite:

        pdf_generados = []

        for archivo in CARPETA_FACTURAS.glob(
            "*.pdf"
        ):

            try:

                modificacion_actual = (
                    archivo.stat().st_mtime_ns
                )


                # PDF completamente nuevo

                if (
                    archivo.name
                    not in pdf_anteriores
                ):

                    pdf_generados.append(
                        archivo
                    )

                    continue


                # PDF existente que Trilay
                # volvió a generar

                if (
                    modificacion_actual
                    >
                    pdf_anteriores[
                        archivo.name
                    ]
                ):

                    pdf_generados.append(
                        archivo
                    )


            except Exception:
                pass


        if (
            len(pdf_generados)
            >= cantidad_esperada
        ):

            break


        time.sleep(2)


    # ==========================================
    # ESPERAR QUE TERMINEN DE ESCRIBIRSE
    # ==========================================

    pdf_listos = []


    for archivo in pdf_generados:

        if _archivo_estable(
            archivo
        ):

            pdf_listos.append(
                archivo
            )


    # ==========================================
    # MOVER PDF
    # ==========================================

    archivos_movidos = []


    for pdf in pdf_listos:

        destino = (
            carpeta_destino
            / pdf.name
        )


        try:

            # Si ya existe una copia dentro
            # de la carpeta del día,
            # reemplazamos por la nueva.

            if destino.exists():

                destino.unlink()


            shutil.move(
                str(pdf),
                str(destino)
            )


            archivos_movidos.append(
                destino
            )


        except Exception as error:

            print(
                f"No se pudo mover "
                f"{pdf.name}: {error}"
            )


    return archivos_movidos


def _archivo_estable(
    archivo: Path,
):

    try:

        tamaño_anterior = (
            archivo.stat().st_size
        )


        time.sleep(2)


        tamaño_actual = (
            archivo.stat().st_size
        )


        return (
            tamaño_anterior
            ==
            tamaño_actual
        )


    except Exception:

        return False