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
from integraciones.correo import enviar_log_por_correo, formatear_reporte_correo
from utils.registro import registrar_ejecucion
from utils.fechas import formatos_fecha_facturacion


def ejecutar_proceso(
    fecha_desde=FECHA_DESDE,
    fecha_carpeta=FECHA_CARPETA,
    reporte=None,
):

    if reporte is None:
        reporte = {}
    facturas = []
    archivos_movidos = []
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

            reporte["observacion"] = "Trilay no mostró facturas para la fecha y el cliente configurados."
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
        reporte["descargadas"] = [archivo.name for archivo in archivos_movidos]


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

        reporte["error_general"] = f"Falló la etapa de Trilay: {type(error).__name__}: {error}"
        for factura in facturas:
            reporte.setdefault("pendientes_detalle", []).append({
                "archivo": str(factura.get("codigo", "Factura sin código")),
                "motivo": "La descarga desde Trilay no terminó correctamente; no se intentó cargar en Krikos.",
            })
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

        resultado_krikos = cargar_facturas_en_krikos(fecha_carpeta)
        if not isinstance(resultado_krikos, dict):
            raise RuntimeError("Krikos no devolvió un resultado verificable.")
        reporte.update(resultado_krikos)
        return not (resultado_krikos.get("errores") or
                    resultado_krikos.get("sin_enviar"))

    except Exception as error:

        print(
            f"Error durante la carga en Krikos: "
            f"{type(error).__name__}: {error}"
        )

        reporte["error_general"] = f"Falló la etapa de Krikos: {type(error).__name__}: {error}"
        for archivo in archivos_movidos:
            reporte.setdefault("pendientes_detalle", []).append({
                "archivo": archivo.name,
                "motivo": "Krikos no pudo procesar el lote; se desconoce si esta factura fue cargada.",
            })
        return False


def main(fecha_facturacion=None):
    resultado_ok = False
    ruta_log = None
    reporte = {}

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
                reporte=reporte,
            )
    except BaseException as error:
        resultado_ok = False
        reporte["error_general"] = f"Error inesperado: {type(error).__name__}: {error}"

    estado = "OK" if resultado_ok else "CON ERRORES"
    asunto = f"Proceso Trilay/Krikos {fecha_carpeta}: {estado}"

    try:
        if ruta_log is None:
            raise RuntimeError("No se pudo crear el archivo de log")

        log_texto = ruta_log.read_text(encoding="utf-8")

        cuerpo = formatear_reporte_correo(
            fecha_carpeta, resultado_ok, reporte, log_texto
        )
        enviar_log_por_correo(asunto, cuerpo)
        print(f"Correo de resultado enviado: {asunto}")
    except Exception as error:
        print(
            "No se pudo enviar el correo de resultado: "
            f"{type(error).__name__}: {error}"
        )
        return False

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
    sys.exit(0 if ejecutar_desde_terminal() else 1)
