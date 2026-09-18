import time

from krikos.login import bloquear_chat
from krikos.validaciones import cerrar_dialogo_archivo_so


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

    subido = False


    try:

        with page.expect_file_chooser(
            timeout=3000
        ) as selector_archivo:

            page.click(
                (
                    'button:has-text('
                    '"SUBA EL PDF DE SU FACTURA"'
                    ')'
                ),
                timeout=3000,
            )


        selector_archivo.value.set_files(
            ruta_pdf
        )


        subido = True


    except Exception:
        pass


    if not subido:

        page.locator(
            "input#fileOriginal"
        ).set_input_files(
            ruta_pdf
        )


    time.sleep(
        0.5
    )


    cerrar_dialogo_archivo_so()


    try:

        page.keyboard.press(
            "Escape"
        )

    except Exception:
        pass


    try:

        page.wait_for_selector(
            (
                'text="Se identificó correctamente '
                'el emisor y receptor del documento"'
            ),
            timeout=15000,
        )

    except Exception:

        # A veces el formulario ya está listo
        # aunque el mensaje no aparezca.
        pass