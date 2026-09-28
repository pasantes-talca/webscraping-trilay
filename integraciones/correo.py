import os
import smtplib
from email.message import EmailMessage

from config import (
    MAIL_DESDE,
    MAIL_PARA,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USAR_SSL,
    SMTP_USUARIO,
)


def formatear_reporte_correo(fecha, resultado_ok, reporte, log_texto):
    """Construye un correo legible con el resultado de cada PDF del lote."""
    exitosas = reporte.get("exitosas_detalle", [])
    ya_cargadas = reporte.get("ya_cargadas_detalle", [])
    errores = reporte.get("errores_detalle", [])
    pendientes = reporte.get("pendientes_detalle", [])
    omitidas = reporte.get("omitidas_detalle", [])

    carpeta_origen = reporte.get("carpeta_origen")
    lineas = [
        f"{'Carga Krikos desde carpeta local' if carpeta_origen else 'Proceso Trilay/Krikos'} - {fecha}",
        f"Estado general: {'OK' if resultado_ok else 'CON ERRORES'}",
        "",
        "Resumen de esta ejecución:",
        (
            f"  PDF encontrados en la carpeta: {len(reporte.get('archivos_entrada', []))}"
            if carpeta_origen else
            f"  PDF descargados desde Trilay: {len(reporte.get('descargadas', []))}"
        ),
        f"  Facturas cargadas y enviadas: {len(exitosas)}",
        f"  Facturas ya cargadas anteriormente en Krikos: {len(ya_cargadas)}",
        f"  Facturas con error: {len(errores)}",
        f"  Facturas pendientes o sin confirmación: {len(pendientes)}",
        f"  Facturas de cambio omitidas: {len(omitidas)}",
    ]

    if carpeta_origen:
        lineas += [f"Carpeta de entrada: {carpeta_origen}"]

    if reporte.get("observacion"):
        lineas += ["", f"Observación: {reporte['observacion']}"]
    if reporte.get("error_general"):
        lineas += ["", f"Error general: {reporte['error_general']}"]
    for error in reporte.get("errores_generales", []):
        lineas += ["", f"Error general: {error}"]

    if reporte.get("provincias"):
        lineas += ["", "RESULTADO POR PROVINCIA"]
        for provincia in reporte["provincias"]:
            lineas.append(
                f"  {provincia['provincia']}: "
                f"descarga={provincia['estado_descarga']}, "
                f"PDF={len(provincia['descargadas'])}, "
                f"Krikos={provincia['estado_krikos']}, "
                f"ya cargadas={provincia.get('ya_cargadas', 0)}"
            )

    if reporte.get("descargadas"):
        lineas += ["", "PDF DESCARGADOS DE TRILAY"]
        for pdf in reporte["descargadas"]:
            if isinstance(pdf, dict):
                lineas.append(f"  - {pdf['provincia']} / {pdf['archivo']}")
            else:
                lineas.append(f"  - {pdf}")

    for titulo, facturas in (
        ("FACTURAS CARGADAS Y ENVIADAS", exitosas),
        ("FACTURAS YA CARGADAS ANTERIORMENTE", ya_cargadas),
        ("FACTURAS CON ERROR", errores),
        ("FACTURAS PENDIENTES O SIN CONFIRMACIÓN", pendientes),
        ("FACTURAS DE CAMBIO OMITIDAS", omitidas),
    ):
        lineas += ["", titulo]
        if not facturas:
            lineas.append("  Ninguna.")
        for factura in facturas:
            identificacion = factura["archivo"]
            if factura.get("provincia"):
                identificacion = f"{factura['provincia']} / {identificacion}"
            if factura.get("numero"):
                identificacion += f" (factura {factura['numero']})"
            lineas.append(f"  - {identificacion}")
            if factura.get("motivo"):
                lineas.append(f"    Motivo: {factura['motivo']}")

    lineas += ["", "REGISTRO COMPLETO", log_texto.strip() or "Sin registro disponible."]
    cuerpo = "\n".join(lineas) + "\n"
    for clave in ("TRILAY_PASSWORD", "KRIKOS_PASSWORD", "PASSWORD",
                  "SERVIDOR_PASSWORD", "SMTP_PASSWORD"):
        secreto = os.getenv(clave)
        if secreto:
            cuerpo = cuerpo.replace(secreto, "********")
    return cuerpo


def enviar_log_por_correo(asunto, cuerpo):
    faltantes = []

    if not SMTP_HOST:
        faltantes.append("SMTP_HOST")
    if not SMTP_USUARIO:
        faltantes.append("SMTP_USUARIO")
    if not SMTP_PASSWORD:
        faltantes.append("SMTP_PASSWORD")
    if not MAIL_DESDE:
        faltantes.append("MAIL_DESDE")
    if not MAIL_PARA:
        faltantes.append("MAIL_PARA")

    if faltantes:
        raise RuntimeError(
            "Falta configurar el correo en .env: "
            + ", ".join(faltantes)
        )

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = MAIL_DESDE
    mensaje["To"] = ", ".join(MAIL_PARA)
    mensaje.set_content(cuerpo)

    cliente_smtp = (
        smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
        if SMTP_USAR_SSL
        else smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
    )

    with cliente_smtp as servidor:
        if not SMTP_USAR_SSL:
            servidor.ehlo()
            servidor.starttls()
            servidor.ehlo()

        servidor.login(SMTP_USUARIO, SMTP_PASSWORD)
        servidor.send_message(mensaje)
