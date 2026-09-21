import sys

from config import (
    FECHA_DESDE,
    FECHA_CARPETA,
    CLIENTE,
    SUCURSAL,
)

from trilay.navegador import crear_driver
from trilay.login import iniciar_sesion

from trilay.ventas import (
    seleccionar_sucursal,
    abrir_ventas,
    aplicar_filtros,
    obtener_facturas,
    seleccionar_facturas,
)

from trilay.impresion import imprimir_facturas_pdf

from archivos.facturas import (
    registrar_pdfs_existentes,
    organizar_pdfs_generados,
)

from integraciones.krikos import cargar_facturas_en_krikos
from integraciones.correo import enviar_log_por_correo
from utils.registro import registrar_ejecucion
from utils.fechas import formatos_fecha_facturacion


def ejecutar_proceso(
    fecha_desde=FECHA_DESDE,
    fecha_carpeta=FECHA_CARPETA,
):

    driver = None

    try:

        print("Iniciando automatización Trilay...")
        print(f"Fecha de proceso: {fecha_desde}")

        driver = crear_driver()

        iniciar_sesion(
            driver
        )

        seleccionar_sucursal(
            driver,
            SUCURSAL
        )

        abrir_ventas(
            driver
        )

        aplicar_filtros(
            driver=driver,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_desde,
            cliente=CLIENTE,
        )

        facturas = obtener_facturas(
            driver=driver,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_desde,
            cliente=CLIENTE,
        )

        if not facturas:

            print(
                "No se encontraron facturas."
            )

            return True

        seleccionar_facturas(
            driver,
            facturas
        )

        pdf_anteriores = (
            registrar_pdfs_existentes()
        )

        imprimir_facturas_pdf(
            driver=driver,
            facturas=facturas,
            sucursal=SUCURSAL,
        )

        archivos_movidos = (
            organizar_pdfs_generados(
                pdf_anteriores=pdf_anteriores,
                cantidad_esperada=len(facturas),
                fecha_carpeta=fecha_carpeta,
            )
        )


        if len(archivos_movidos) != len(facturas):

            raise Exception(
                "No se generaron todos los PDF esperados. "
                f"Esperados: {len(facturas)}. "
                f"Organizados: {len(archivos_movidos)}. "
                "No se iniciara Krikos."
            )


        print(
            f"Descarga de Trilay completada. "
            f"Facturas procesadas: {len(facturas)}. "
            f"PDF organizados: {len(archivos_movidos)}."
        )

    except Exception as error:

        print(
            f"Error durante la automatización: "
            f"{type(error).__name__}: {error}"
        )

        return False

    finally:

        if driver is not None:

            try:

                driver.quit()

            except Exception:

                pass


    # El driver de Internet Explorer ya esta cerrado en este punto.
    # Krikos puede abrir su navegador y procesar la carpeta del dia.
    try:

        cargar_facturas_en_krikos(fecha_carpeta)

    except Exception as error:

        print(
            f"Error durante la carga en Krikos: "
            f"{type(error).__name__}: {error}"
        )

        return False

    return True


def main(fecha_facturacion=None):
    resultado_ok = False
    ruta_log = None

    try:
        fecha_desde, fecha_carpeta = formatos_fecha_facturacion(
            fecha_facturacion
        )
    except ValueError as error:
        print(error)
        return False

    try:
        with registrar_ejecucion() as ruta_log:
            resultado_ok = ejecutar_proceso(
                fecha_desde=fecha_desde,
                fecha_carpeta=fecha_carpeta,
            )
    except BaseException:
        resultado_ok = False

    estado = "OK" if resultado_ok else "CON ERRORES"
    asunto = f"Proceso Trilay/Krikos {fecha_carpeta}: {estado}"

    try:
        if ruta_log is None:
            raise RuntimeError("No se pudo crear el archivo de log")

        log_texto = ruta_log.read_text(encoding="utf-8")

        # Extract the structured summary printed by webscrapping
        MARCA_INI = "=== RESUMEN CORREO ==="
        MARCA_FIN = "=== FIN RESUMEN CORREO ==="
        idx_ini = log_texto.find(MARCA_INI)
        idx_fin = log_texto.find(MARCA_FIN)
        if idx_ini != -1 and idx_fin != -1:
            cuerpo = log_texto[idx_ini + len(MARCA_INI):idx_fin].strip()
        else:
            cuerpo = log_texto
        enviar_log_por_correo(asunto, cuerpo)
        print(f"Correo de resultado enviado: {asunto}")
    except Exception as error:
        print(
            "No se pudo enviar el correo de resultado: "
            f"{type(error).__name__}: {error}"
        )

    return resultado_ok


def ejecutar_desde_terminal(argumentos=None):
    argumentos = list(sys.argv[1:] if argumentos is None else argumentos)

    if len(argumentos) > 1:
        print(
            "Uso: python main.py [DD-MM-AAAA]\n"
            "Ejemplo: python main.py 17-09-2026"
        )
        return False

    fecha_facturacion = argumentos[0] if argumentos else None
    return main(fecha_facturacion)


if __name__ == "__main__":
    ejecutar_desde_terminal()
