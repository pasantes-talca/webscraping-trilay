import hashlib
import os
import shutil
import subprocess
import tempfile

from datetime import datetime
from pathlib import Path

from config import (
    CARPETA_FACTURAS,
    SERVIDOR_USUARIO,
    SERVIDOR_PASSWORD,
)


def carpeta_del_dia(
    raiz,
    fecha=None,
):

    nombre = (
        fecha
        or datetime.now()
    ).strftime(
        "%d-%m-%Y"
    )

    raiz = Path(
        raiz
    )

    carpeta = (
        raiz
        if raiz.name == nombre
        else raiz / nombre
    )

    if not carpeta.is_dir():

        raise RuntimeError(
            "No existe la carpeta de "
            f"facturas del día: {carpeta}"
        )

    return carpeta


def listar_pdf(
    carpeta,
):

    carpeta = Path(
        carpeta
    )

    return sorted(
        archivo
        for archivo in carpeta.iterdir()
        if (
            archivo.is_file()
            and
            archivo.suffix.lower()
            == ".pdf"
        )
    )


def conectar_servidor():

    carpeta = Path(
        CARPETA_FACTURAS
    )

    try:

        listar_pdf(
            carpeta
        )

    except OSError:

        if (
            not SERVIDOR_USUARIO
            or
            not SERVIDOR_PASSWORD
        ):

            raise RuntimeError(
                "No se puede acceder al servidor "
                "y faltan las credenciales "
                "del servidor."
            ) from None


        try:

            resultado = subprocess.run(
                [
                    "net",
                    "use",
                    str(carpeta),
                    SERVIDOR_PASSWORD,
                    f"/user:{SERVIDOR_USUARIO}",
                    "/persistent:no",
                ],
                capture_output=True,
                text=True,
                errors="replace",
                timeout=30,
            )

        except (
            OSError,
            subprocess.TimeoutExpired,
        ):

            raise RuntimeError(
                "No se pudo conectar al "
                "servidor o la conexión "
                "superó los 30 segundos."
            ) from None


        if resultado.returncode:

            detalle = (
                resultado.stderr
                or resultado.stdout
            )

            if SERVIDOR_PASSWORD:

                detalle = detalle.replace(
                    SERVIDOR_PASSWORD,
                    "********"
                )

            raise RuntimeError(
                "Error conectando al servidor "
                f"({resultado.returncode}): "
                f"{detalle}"
            )


        listar_pdf(
            carpeta
        )


    return carpeta


def huella(
    ruta,
):

    digest = hashlib.sha256()


    with open(
        ruta,
        "rb",
    ) as archivo:

        for bloque in iter(
            lambda:
                archivo.read(
                    1024 * 1024
                ),
            b"",
        ):

            digest.update(
                bloque
            )


    return digest.hexdigest()


def importar_pdf(
    carpeta_servidor,
    carpeta_pendientes,
    carpetas_locales,
):

    origen = Path(
        carpeta_servidor
    ).resolve()


    carpetas_locales = [
        Path(carpeta).resolve()
        for carpeta
        in carpetas_locales
    ]


    if origen in carpetas_locales:

        raise RuntimeError(
            "La carpeta del servidor debe "
            "ser distinta de las carpetas "
            "locales de facturas."
        )


    # ==========================================
    # CREAR CARPETA PENDIENTES
    # ==========================================

    carpeta_pendientes = Path(
        carpeta_pendientes
    )

    carpeta_pendientes.mkdir(
        parents=True,
        exist_ok=True,
    )


    # ==========================================
    # CALCULAR FACTURAS YA CONOCIDAS
    # ==========================================

    conocidas = set()


    for carpeta in carpetas_locales:

        if not carpeta.exists():
            continue


        for pdf in listar_pdf(
            carpeta
        ):

            try:

                conocidas.add(
                    huella(pdf)
                )

            except Exception:
                pass


    importados = 0
    omitidos = 0
    errores = 0


    # ==========================================
    # IMPORTAR PDF
    # ==========================================

    for pdf in listar_pdf(
        origen
    ):

        temporal = None


        try:

            # Estado del PDF antes de copiar.
            antes = pdf.stat()


            firma = huella(
                pdf
            )


            # Ya fue procesado/importado.
            if firma in conocidas:

                omitidos += 1

                continue


            # ==================================
            # COPIA TEMPORAL
            # ==================================

            fd, temporal = tempfile.mkstemp(
                dir=carpeta_pendientes,
                suffix=".part",
            )


            os.close(
                fd
            )


            shutil.copyfile(
                pdf,
                temporal,
            )


            # ==================================
            # VERIFICAR QUE EL PDF NO CAMBIÓ
            # ==================================

            despues = pdf.stat()


            if (
                (
                    antes.st_size,
                    antes.st_mtime_ns,
                )
                !=
                (
                    despues.st_size,
                    despues.st_mtime_ns,
                )
                or
                huella(
                    temporal
                )
                != firma
            ):

                raise RuntimeError(
                    "El PDF cambió durante "
                    "la copia. Se reintentará "
                    "en la próxima ejecución."
                )


            # ==================================
            # DEFINIR DESTINO
            # ==================================

            destino = (
                carpeta_pendientes
                / pdf.name
            )


            contador = 1


            while destino.exists():

                destino = (
                    carpeta_pendientes
                    /
                    (
                        f"{pdf.stem}_"
                        f"{contador}"
                        f"{pdf.suffix}"
                    )
                )

                contador += 1


            # Renombramos el .part solamente
            # cuando la copia fue validada.

            os.rename(
                temporal,
                destino,
            )


            temporal = None


            conocidas.add(
                firma
            )


            importados += 1


        except (
            OSError,
            RuntimeError,
        ):

            errores += 1


        finally:

            if (
                temporal
                is not None
            ):

                try:

                    Path(
                        temporal
                    ).unlink(
                        missing_ok=True
                    )

                except Exception:
                    pass


    return {
        "importados": importados,
        "omitidos": omitidos,
        "errores": errores,
    }