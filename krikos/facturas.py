import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from krikos.login import bloquear_chat


def abrir_nueva_factura(
    page,
    krikos_url,
):

    page.goto(
        krikos_url
    )

    page.wait_for_selector(
        "#boton-nuevo-documento",
        timeout=20000,
    )

    bloquear_chat(
        page
    )


    page.click(
        "#boton-nuevo-documento"
    )


    page.wait_for_selector(
        (
            'button.mat-mdc-menu-item:has-text("Factura"), '
            'button.mat-menu-item:has-text("Factura")'
        ),
        timeout=7000,
    )


    opcion = page.locator(
        (
            'button.mat-mdc-menu-item:has-text("Factura"), '
            'button.mat-menu-item:has-text("Factura")'
        )
    ).first


    opcion.click()


    page.wait_for_selector(
        'text="Crear Factura"',
        timeout=15000,
    )


    bloquear_chat(
        page
    )


def subir_pdf(
    page,
    ruta_pdf,
):

    # Enviar bytes evita que Edge mantenga abierto el PDF original en Windows/SMB.
    ruta = Path(ruta_pdf)
    for intento in range(5):
        try:
            contenido = ruta.read_bytes()
            break
        except PermissionError:
            if intento == 4:
                raise
            time.sleep(1)
    archivo = {"name": ruta.name, "mimeType": "application/pdf", "buffer": contenido}
    campo = page.locator("input#fileOriginal")
    if campo.count():
        campo.set_input_files(archivo)
    else:
        with page.expect_file_chooser(timeout=5000) as selector:
            page.get_by_role("button", name="SUBA EL PDF DE SU FACTURA").click()
        selector.value.set_files(archivo)

    try:
        page.locator('input[formcontrolname="ptoVta"]').wait_for(
            state="visible", timeout=45000,
        )
    except PlaywrightTimeoutError as error:
        raise PlaywrightTimeoutError(
            "Krikos no habilitó el encabezado después de adjuntar el PDF "
            f"{ruta.name}. URL: {page.url}"
        ) from error
