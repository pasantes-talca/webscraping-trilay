import os

from dotenv import load_dotenv

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import BASE_DIR


load_dotenv(
    BASE_DIR / ".env"
)


USUARIO = os.getenv(
    "TRILAY_USUARIO"
)

PASSWORD = os.getenv(
    "TRILAY_PASSWORD"
)


if not USUARIO or not PASSWORD:

    raise ValueError(
        "No se encontraron las credenciales "
        "de Trilay en el archivo .env"
    )


def iniciar_sesion(driver):

    espera = WebDriverWait(
        driver,
        30
    )


    campo_usuario = espera.until(
        EC.presence_of_element_located(
            (
                By.ID,
                "txtUsuario"
            )
        )
    )


    campo_password = espera.until(
        EC.presence_of_element_located(
            (
                By.ID,
                "txtPass"
            )
        )
    )


    campo_usuario.clear()

    campo_usuario.send_keys(
        USUARIO
    )


    campo_password.clear()

    campo_password.send_keys(
        PASSWORD
    )


    boton_login = espera.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[normalize-space()='Ingresar']"
            )
        )
    )


    boton_login.click()


    WebDriverWait(
        driver,
        60
    ).until(
        lambda navegador:
            "escritorio.asp"
            in navegador.current_url.lower()
    )