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
