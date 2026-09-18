from config import (
    FECHA_DESDE,
    FECHA_HASTA,
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


def ejecutar_proceso():

    driver = None

    try:

        print("Iniciando automatización Trilay...")
        print(f"Fecha de proceso: {FECHA_DESDE}")

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
            fecha_desde=FECHA_DESDE,
            fecha_hasta=FECHA_HASTA,
            cliente=CLIENTE,
        )

        facturas = obtener_facturas(
            driver=driver,
            fecha_desde=FECHA_DESDE,
            fecha_hasta=FECHA_HASTA,
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
                fecha_carpeta=FECHA_CARPETA,
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

        cargar_facturas_en_krikos(FECHA_CARPETA)

    except Exception as error:

        print(
            f"Error durante la carga en Krikos: "
            f"{type(error).__name__}: {error}"
        )

        return False

    return True


def main():
    resultado_ok = False
    ruta_log = None

    try:
        with registrar_ejecucion() as ruta_log:
            resultado_ok = ejecutar_proceso()
    except BaseException:
        resultado_ok = False

    estado = "OK" if resultado_ok else "CON ERRORES"
    asunto = f"Proceso Trilay/Krikos {FECHA_CARPETA}: {estado}"

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


if __name__ == "__main__":
    main()
