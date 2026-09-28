import sys
from datetime import date

from config import (
    BASE_DIR,
    CARPETA_FACTURAS,
    CLIENTE,
    FECHA_CARPETA,
    FECHA_DESDE,
    SUCURSALES_ORDEN,
)
from trilay.sesion_headless import SesionTrilay
from archivos.facturas import registrar_pdfs_existentes, organizar_pdfs_generados
from integraciones.krikos import cargar_facturas_en_krikos
from krikos.servidor import conectar_servidor
from krikos.proceso import cerrar_sesion_krikos, procesar_carpeta_local_krikos
from integraciones.correo import enviar_log_por_correo, formatear_reporte_correo
from utils.registro import registrar_ejecucion
from utils.fechas import formatos_fecha_facturacion


DETALLES_KRIKOS = (
    "exitosas_detalle",
    "ya_cargadas_detalle",
    "errores_detalle",
    "pendientes_detalle",
    "omitidas_detalle",
)

CARPETA_CARGA_MANUAL = BASE_DIR / "facturas a cargar"


def descargar_provincia(provincia, fecha_desde, fecha_carpeta, reporte, sesion):
    """Busca y descarga las facturas de una provincia sin afectar a las demás."""
    estado = {
        "provincia": provincia,
        "descargadas": [],
        "estado_descarga": "error",
        "estado_krikos": "omitido",
        "apta_krikos": False,
    }
    facturas = []
    try:
        print(f"\nTrilay: buscando facturas de {provincia} para {fecha_desde}...")
        facturas = sesion.buscar_facturas(provincia, fecha_desde, CLIENTE)

        if not facturas:
            print(f"Trilay: no se encontraron facturas de {provincia}.")
            estado["estado_descarga"] = "sin_facturas"
            # Permite procesar facturas pendientes de una ejecución anterior.
            estado["apta_krikos"] = (
                CARPETA_FACTURAS / provincia / fecha_carpeta
            ).is_dir()
            return estado

        for indice, factura in enumerate(facturas, start=1):
            print(f"Trilay: PDF {indice}/{len(facturas)} de {provincia}, código {factura['codigo']}")
            pdf_anteriores = registrar_pdfs_existentes()
            sesion.imprimir_factura(factura, provincia)
            archivos_movidos = organizar_pdfs_generados(
                pdf_anteriores=pdf_anteriores,
                cantidad_esperada=1,
                fecha_carpeta=fecha_carpeta,
                provincia=provincia,
            )
            if len(archivos_movidos) != 1:
                raise RuntimeError(
                    f"No se guardó el PDF de la factura {factura['codigo']}"
                )
            archivo = archivos_movidos[0]
            estado["descargadas"].append(archivo.name)
            reporte.setdefault("descargadas", []).append({
                "provincia": provincia, "archivo": archivo.name,
            })

        print(f"Trilay: {len(estado['descargadas'])} PDF de {provincia} guardados.")
        estado["estado_descarga"] = "ok"
        estado["apta_krikos"] = True
        return estado

    except Exception as error:
        motivo = f"Trilay no completó {provincia}: {type(error).__name__}: {error}"
        print(motivo)
        estado["error"] = motivo
        reporte.setdefault("errores_generales", []).append(motivo)
        estado["apta_krikos"] = bool(estado["descargadas"]) or (
            CARPETA_FACTURAS / provincia / fecha_carpeta
        ).is_dir()
        for indice, factura in enumerate(
            facturas[len(estado["descargadas"]):]
        ):
            reporte.setdefault("pendientes_detalle", []).append({
                "provincia": provincia,
                "archivo": str(factura.get("codigo", "Factura sin código")),
                "motivo": (
                    f"No se pudo generar o guardar el PDF: {type(error).__name__}: {error}"
                    if indice == 0 else
                    "No se intentó descargar porque falló la factura anterior."
                ),
            })
        return estado


def ejecutar_proceso(
    fecha_desde=FECHA_DESDE,
    fecha_carpeta=FECHA_CARPETA,
    reporte=None,
):
    if reporte is None:
        reporte = {}
    reporte["provincias"] = []
    resultado_ok = True

    # La impresora PDF de Trilay escribe en el recurso de red.
    conectar_servidor()

    # Primero terminan todas las descargas de Trilay.
    with SesionTrilay() as sesion_trilay:
        for provincia in SUCURSALES_ORDEN:
            estado = descargar_provincia(
                provincia, fecha_desde, fecha_carpeta, reporte, sesion_trilay
            )
            reporte["provincias"].append(estado)
            if estado["estado_descarga"] == "error":
                resultado_ok = False

    # La misma página de Krikos procesa Mendoza, San Juan y San Luis.
    sesion_krikos = {}
    try:
        return _cargar_provincias(
            reporte, fecha_carpeta, resultado_ok, sesion_krikos
        )
    finally:
        cerrar_sesion_krikos(sesion_krikos)


def _cargar_provincias(reporte, fecha_carpeta, resultado_ok, sesion_krikos):
    for estado in reporte["provincias"]:
        if not estado["apta_krikos"]:
            continue
        provincia = estado["provincia"]
        try:
            print(f"\nKrikos: cargando facturas de {provincia}...")
            resultado = cargar_facturas_en_krikos(
                fecha_carpeta, provincia, sesion_krikos
            )
            if not isinstance(resultado, dict):
                raise RuntimeError("Krikos no devolvió un resultado verificable.")

            for clave in DETALLES_KRIKOS:
                reporte.setdefault(clave, []).extend(
                    {**factura, "provincia": provincia}
                    for factura in resultado.get(clave, [])
                )
            estado["enviadas"] = resultado.get("enviadas", 0)
            estado["ya_cargadas"] = resultado.get("ya_cargadas", 0)
            estado["errores"] = resultado.get("errores", 0)
            estado["sin_enviar"] = resultado.get("sin_enviar", 0)
            if resultado.get("errores") or resultado.get("sin_enviar"):
                estado["estado_krikos"] = "con_errores"
                resultado_ok = False
            else:
                estado["estado_krikos"] = "ok"

        except Exception as error:
            motivo = f"Krikos no completó {provincia}: {type(error).__name__}: {error}"
            print(motivo)
            estado["estado_krikos"] = "error"
            estado["error_krikos"] = motivo
            reporte.setdefault("errores_generales", []).append(motivo)
            for archivo in estado["descargadas"]:
                reporte.setdefault("pendientes_detalle", []).append({
                    "provincia": provincia,
                    "archivo": archivo,
                    "motivo": "Krikos no completó el lote; verificar si esta factura se cargó antes de reintentar.",
                })
            resultado_ok = False

    return resultado_ok


def main_trilay(fecha_facturacion=None):
    resultado_ok = False
    ruta_log = None
    reporte = {}

    try:
        fecha_desde, fecha_carpeta = formatos_fecha_facturacion(fecha_facturacion)
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


def main():
    """Carga exclusivamente los PDF de la carpeta local de carga manual."""
    resultado_ok = False
    ruta_log = None
    fecha_carpeta = date.today().strftime("%d-%m-%Y")
    reporte = {"carpeta_origen": str(CARPETA_CARGA_MANUAL)}

    try:
        with registrar_ejecucion() as ruta_log:
            if not CARPETA_CARGA_MANUAL.is_dir():
                raise FileNotFoundError(
                    f"No existe la carpeta de facturas a cargar: {CARPETA_CARGA_MANUAL}"
                )

            archivos = sorted(
                archivo for archivo in CARPETA_CARGA_MANUAL.iterdir()
                if archivo.is_file() and archivo.suffix.lower() == ".pdf"
            )
            reporte["archivos_entrada"] = [archivo.name for archivo in archivos]
            print(f"Krikos: {len(archivos)} PDF en {CARPETA_CARGA_MANUAL}")
            resultado = procesar_carpeta_local_krikos(CARPETA_CARGA_MANUAL)
            for clave in DETALLES_KRIKOS:
                reporte[clave] = resultado.get(clave, [])
            resultado_ok = not resultado.get("errores") and not resultado.get("sin_enviar")
    except BaseException as error:
        reporte["error_general"] = f"Error inesperado: {type(error).__name__}: {error}"

    estado = "OK" if resultado_ok else "CON ERRORES"
    asunto = f"Carga Krikos desde carpeta local {fecha_carpeta}: {estado}"
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
    if not argumentos:
        return main_trilay()
    if argumentos == ["--carpeta"]:
        return main()
    if len(argumentos) == 1 and not argumentos[0].startswith("-"):
        return main_trilay(argumentos[0])
    print("Uso: python main.py [DD-MM-AAAA | --carpeta]")
    return False


if __name__ == "__main__":
    sys.exit(0 if ejecutar_desde_terminal() else 1)
