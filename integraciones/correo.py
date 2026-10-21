import os
import smtplib
from html import escape
import re
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


def _sin_secretos(texto):
    for clave in ("TRILAY_PASSWORD", "KRIKOS_PASSWORD", "PASSWORD",
                  "SERVIDOR_PASSWORD", "SMTP_PASSWORD"):
        secreto = os.getenv(clave)
        if secreto:
            texto = texto.replace(secreto, "********")
    return texto


def _motivo_breve(motivo):
    texto = str(motivo or "").lower()
    if "sin confirmar" in texto or "no confirm" in texto or "se pulsó enviar" in texto:
        return "Ingreso sin confirmar; revisar en Krikos antes de reintentar"
    if "diferencias" in texto:
        return "Krikos pidió revisar diferencias en los importes"
    if "desactivado" in texto:
        return "El envío automático está desactivado"
    if any(valor in texto for valor in ("winerror 32", "utilizado por otro proceso", "permissionerror", "bloqueado")):
        return "Archivo PDF bloqueado; no se pudo completar el proceso"
    if any(valor in texto for valor in ("ptovta", "formulario", "encabezado")):
        return "El formulario de Krikos no estuvo disponible"
    if any(valor in texto for valor in ("gln", "extraer", "no contiene productos", "no se pudieron extraer", "no se pudo determinar", "datos incompletos")):
        return "Datos de la factura incompletos o no reconocidos"
    if "iniciar" in texto and "krikos" in texto:
        return "No se pudo iniciar la sesión en Krikos"
    if "generar o guardar" in texto or "descargar" in texto:
        return "No se pudo descargar o guardar el PDF"
    if "verificar" in texto and "reintentar" in texto:
        return "Ingreso sin confirmar; revisar en Krikos antes de reintentar"
    return "No se pudo completar la carga; requiere revisión"


def _factura_visible(factura):
    if not isinstance(factura, dict):
        factura = {"archivo": str(factura)}
    # Los reportes muestran solo nombres, nunca rutas locales o del servidor.
    archivo = str(factura.get("archivo") or "Factura sin identificar").replace("\\", "/").rsplit("/", 1)[-1]
    numero = str(factura.get("numero") or "")
    if not numero:
        coincidencia = re.search(r"(?:FA)?(\d{4,5}-\d{8})", archivo, re.IGNORECASE)
        if coincidencia:
            numero = coincidencia.group(1)
    return {"archivo": archivo, "numero": numero,
            "provincia": str(factura.get("provincia") or "")}


def _secciones_reporte(reporte):
    manual = bool(reporte.get("carpeta_origen"))
    entradas = reporte.get("archivos_entrada", []) if manual else reporte.get("descargadas", [])
    descargadas = [_factura_visible(f) for f in entradas]
    enviadas = [_factura_visible(f) for f in reporte.get("exitosas_detalle", [])]
    omitidas = []
    for factura in reporte.get("ya_cargadas_detalle", []):
        omitidas.append({**_factura_visible(factura), "motivo": "Ya estaba ingresada en Krikos"})
    for factura in reporte.get("omitidas_detalle", []):
        motivo = str(factura.get("motivo") or "").lower()
        omitidas.append({**_factura_visible(factura), "motivo": (
            "Documento de cambio" if "cambio" in motivo else "Omitida por las reglas del proceso"
        )})
    fallidas = []
    for clave in ("errores_detalle", "pendientes_detalle"):
        for factura in reporte.get(clave, []):
            fallidas.append({**_factura_visible(factura),
                             "motivo": _motivo_breve(factura.get("motivo"))})
    return [
        ("Encontradas en la carpeta" if manual else "Descargadas", descargadas, "#2563eb", "#eff6ff"),
        ("Enviadas", enviadas, "#15803d", "#f0fdf4"),
        ("Omitidas", omitidas, "#a16207", "#fffbeb"),
        ("No se pudieron cargar", fallidas, "#b91c1c", "#fef2f2"),
    ]


def _identificacion(factura):
    texto = factura["archivo"]
    if factura["provincia"]:
        texto = f"{factura['provincia']} / {texto}"
    if factura["numero"]:
        texto += f" (factura {factura['numero']})"
    return texto


def _aviso_reporte(resultado_ok, reporte):
    if reporte.get("error_general") or reporte.get("errores_generales"):
        return "El proceso no pudo completarse. El listado puede estar incompleto y requiere revisión."
    if not resultado_ok:
        return "Hay facturas que requieren revisión. Consultá los motivos indicados abajo."
    return ""


def formatear_reporte_correo(fecha, resultado_ok, reporte, log_texto=None):
    """Alternativa de texto simple. log_texto se admite por compatibilidad y se ignora."""
    secciones = _secciones_reporte(reporte)
    lineas = [f"Reporte de facturas · {fecha}"]
    aviso = _aviso_reporte(resultado_ok, reporte)
    if aviso:
        lineas += ["", aviso]
    for titulo, facturas, _, _ in secciones:
        lineas += ["", f"{titulo}: {len(facturas)}"]
        if not facturas:
            lineas.append("  Ninguna")
        for factura in facturas:
            lineas.append(f"  - {_identificacion(factura)}")
            if factura.get("motivo"):
                lineas.append(f"    Motivo: {factura['motivo']}")
    return _sin_secretos("\n".join(lineas) + "\n")


def formatear_reporte_correo_html(fecha, resultado_ok, reporte):
    """Reporte HTML sin recursos externos, apto para clientes de correo."""
    secciones = _secciones_reporte(reporte)
    partes = [
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1"></head>'
        '<body style="margin:0;padding:0;background-color:#f1f5f9;color:#1e293b;font-family:Arial,Helvetica,sans-serif;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9;"><tr><td align="center" style="padding:24px 12px;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:680px;background-color:#ffffff;border:1px solid #e2e8f0;border-radius:12px;">'
        '<tr><td style="padding:28px 24px;background-color:#0f172a;border-radius:12px 12px 0 0;">'
        '<p style="margin:0 0 8px;color:#cbd5e1;font-size:12px;letter-spacing:2px;">TRILAY / KRIKOS</p>'
        '<h1 style="margin:0;color:#ffffff;font-size:26px;">Reporte de facturas</h1>'
        f'<p style="margin:10px 0 0;color:#cbd5e1;font-size:15px;">{escape(_sin_secretos(str(fecha)))}</p></td></tr>'
    ]
    aviso = _aviso_reporte(resultado_ok, reporte)
    if aviso:
        partes.append(f'<tr><td style="padding:20px 24px 0;color:#9a3412;font-size:14px;line-height:1.6;">{escape(aviso)}</td></tr>')
    for titulo, facturas, color, fondo in secciones:
        partes.append(
            '<tr><td style="padding:20px 24px 0;">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:8px;">'
            f'<tr><td style="padding:14px 16px;background-color:{fondo};border-left:4px solid {color};">'
            f'<h2 style="margin:0;font-size:17px;color:{color};">{escape(titulo)} '
            f'<span style="font-size:22px;">{len(facturas)}</span></h2></td></tr>'
        )
        if not facturas:
            partes.append('<tr><td style="padding:14px 16px;color:#64748b;font-size:14px;">Ninguna</td></tr>')
        for factura in facturas:
            partes.append('<tr><td style="padding:14px 16px;border-top:1px solid #e2e8f0;font-size:14px;line-height:1.6;overflow-wrap:anywhere;">'
                          f'{escape(_sin_secretos(_identificacion(factura)))}')
            if factura.get("motivo"):
                partes.append(f'<br><span style="color:#64748b;">{escape(factura["motivo"])}</span>')
            partes.append('</td></tr>')
        partes.append('</table></td></tr>')
    partes.append('<tr><td style="height:24px;font-size:1px;">&nbsp;</td></tr></table></td></tr></table></body></html>')
    return "".join(partes)


def enviar_log_por_correo(asunto, cuerpo, cuerpo_html=None):
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
    if cuerpo_html is not None:
        mensaje.add_alternative(cuerpo_html, subtype="html")

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
