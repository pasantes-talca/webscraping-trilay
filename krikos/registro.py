import os
import sys

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


# ==========================================
# CARPETA DE LOGS
# ==========================================

BASE_KRIKOS = (
    Path(__file__)
    .resolve()
    .parent
)

CARPETA_LOGS = (
    BASE_KRIKOS
    / "logs"
)


# ==========================================
# VALORES SENSIBLES A OCULTAR
# ==========================================

def obtener_secretos():

    secretos = []

    for variable in (
        "TRILAY_PASSWORD",
        "KRIKOS_PASSWORD",
        "SERVIDOR_PASSWORD",
    ):

        valor = os.getenv(
            variable
        )

        if valor:

            secretos.append(
                valor
            )

    return secretos


def ocultar_secretos(
    texto,
):

    texto = str(
        texto
    )

    for secreto in obtener_secretos():

        texto = texto.replace(
            secreto,
            "********"
        )

    return texto


# ==========================================
# ESCRITOR DOBLE:
# CONSOLA + ARCHIVO
# ==========================================

class SalidaDoble:

    def __init__(
        self,
        consola,
        archivo,
    ):

        self.consola = consola

        self.archivo = archivo


    def write(
        self,
        texto,
    ):

        texto_seguro = (
            ocultar_secretos(
                texto
            )
        )


        self.consola.write(
            texto_seguro
        )


        self.archivo.write(
            texto_seguro
        )


    def flush(
        self,
    ):

        self.consola.flush()

        self.archivo.flush()


# ==========================================
# REGISTRO DE EJECUCIÓN
# ==========================================

@contextmanager
def registrar_ejecucion():

    CARPETA_LOGS.mkdir(
        parents=True,
        exist_ok=True,
    )


    fecha = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )


    archivo_log = (
        CARPETA_LOGS
        /
        f"ejecucion_{fecha}.log"
    )


    stdout_original = (
        sys.stdout
    )

    stderr_original = (
        sys.stderr
    )


    with open(
        archivo_log,
        "a",
        encoding="utf-8",
    ) as archivo:

        salida = SalidaDoble(
            stdout_original,
            archivo,
        )


        error = SalidaDoble(
            stderr_original,
            archivo,
        )


        sys.stdout = salida

        sys.stderr = error


        try:

            print(
                "=" * 60
            )

            print(
                "INICIO DE EJECUCIÓN"
            )

            print(
                datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S"
                )
            )

            print(
                "=" * 60
            )


            yield


        finally:

            print(
                "\n"
                + "=" * 60
            )

            print(
                "FIN DE EJECUCIÓN"
            )

            print(
                datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S"
                )
            )

            print(
                "=" * 60
            )


            sys.stdout = (
                stdout_original
            )

            sys.stderr = (
                stderr_original
            )