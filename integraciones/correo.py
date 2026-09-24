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
    errores = reporte.get("errores_detalle", [])
    pendientes = reporte.get("pendientes_detalle", [])
    omitidas = reporte.get("omitidas_detalle", [])

    lineas = [
        f"Proceso Trilay/Krikos - {fecha}",
        f"Estado general: {'OK' if resultado_ok else 'CON ERRORES'}",
        "",
        "Resumen de esta ejecución:",
        f"  PDF descargados desde Trilay: {len(reporte.get('descargadas', []))}",
        f"  Facturas cargadas y enviadas: {len(exitosas)}",
        f"  Facturas con error: {len(errores)}",
        f"  Facturas pendientes o sin confirmación: {len(pendientes)}",
        f"  Facturas de cambio omitidas: {len(omitidas)}",
    ]

    if reporte.get("observacion"):
        lineas += ["", f"Observación: {reporte['observacion']}"]
    if reporte.get("error_general"):
        lineas += ["", f"Error general: {reporte['error_general']}"]

    for titulo, facturas in (
        ("FACTURAS CARGADAS Y ENVIADAS", exitosas),
        ("FACTURAS CON ERROR", errores),
        ("FACTURAS PENDIENTES O SIN CONFIRMACIÓN", pendientes),
        ("FACTURAS DE CAMBIO OMITIDAS", omitidas),
    ):
        lineas += ["", titulo]
        if not facturas:
            lineas.append("  Ninguna.")
        for factura in facturas:
            identificacion = factura["archivo"]
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
