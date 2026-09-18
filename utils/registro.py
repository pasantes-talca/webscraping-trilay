import os
import sys
import traceback
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path


class SalidaConLog:
    def __init__(self, consola, archivo):
        self.consola = consola
        self.archivo = archivo

    def write(self, texto):
        longitud = len(texto)

        for clave in (
            "TRILAY_PASSWORD",
            "PASSWORD",
            "SERVIDOR_PASSWORD",
            "SMTP_PASSWORD",
        ):
            secreto = os.getenv(clave)
            if secreto:
                texto = texto.replace(secreto, "********")

        self.archivo.write(texto)
        self.archivo.flush()

        if self.consola is not None:
            self.consola.write(texto)

        return longitud

    def flush(self):
        self.archivo.flush()
        if self.consola is not None:
            self.consola.flush()


@contextmanager
def registrar_ejecucion():
    carpeta = Path(__file__).resolve().parents[1] / "logs"
    carpeta.mkdir(exist_ok=True)
    ruta = carpeta / f"proceso_{datetime.now():%Y-%m-%d_%H-%M-%S_%f}.txt"

    with ruta.open("x", encoding="utf-8") as archivo:
        with redirect_stdout(SalidaConLog(sys.stdout, archivo)), redirect_stderr(
            SalidaConLog(sys.stderr, archivo)
        ):
            print(f"Inicio: {datetime.now():%Y-%m-%d %H:%M:%S}")
            print(f"Log: {ruta}")
            try:
                yield ruta
            except BaseException:
                traceback.print_exc()
                raise
            finally:
                print(f"Fin: {datetime.now():%Y-%m-%d %H:%M:%S}")
