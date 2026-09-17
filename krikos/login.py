import os

from config import (
    CARPETA_DATA,
    ARCHIVO_ESTADO_SESION,
    KRIKOS_EMAIL,
    KRIKOS_PASSWORD,
    KRIKOS_URL,
)


def bloquear_chat(page):

    try:

        page.add_style_tag(
            content="""
                button[data-testid="launcher"],
                [data-testid="launcher"],
                [aria-label="Chat"] {
                    display: none !important;
                    visibility: hidden !important;
                    pointer-events: none !important;
                }
            """
        )

    except Exception:
        pass


    try:

        page.evaluate(
            """
            () => {

                const bloquear = () => {

                    const selectores = [

                        'button[data-testid="launcher"]',

                        '[data-testid="launcher"]',

                        'button[aria-label="Chat"]'
                    ];


                    for (
                        const selector
                        of selectores
                    ) {

                        document
                            .querySelectorAll(
                                selector
                            )
                            .forEach(
                                el => {

                                    el.style.display =
                                        'none';

                                    el.style.visibility =
                                        'hidden';

                                    el.style.pointerEvents =
                                        'none';

                                    el.setAttribute(
                                        'disabled',
                                        'disabled'
                                    );
                                }
                            );
                    }
                };


                bloquear();


                if (
                    !window.__chatBlockObserver
                ) {

                    window.__chatBlockObserver =
                        new MutationObserver(
                            bloquear
                        );


                    window.__chatBlockObserver
                        .observe(
                            document.body,
                            {
                                childList: true,
                                subtree: true
                            }
                        );
                }
            }
            """
        )

    except Exception:
        pass


def iniciar_sesion_krikos(
    page,
):

    page.goto(
        KRIKOS_URL
    )


    bloquear_chat(
        page
    )


    # Si ya hay sesión iniciada,
    # no hacemos login otra vez.

    if (
        page.locator(
            "#boton-nuevo-documento"
        ).count()
        > 0
    ):

        try:

            page.locator(
                "#boton-nuevo-documento"
            ).wait_for(
                state="visible",
                timeout=4000,
            )

            return

        except Exception:
            pass


    page.wait_for_selector(
        'input[placeholder="Email"]',
        timeout=15000,
    )


    page.fill(
        'input[placeholder="Email"]',
        KRIKOS_EMAIL,
    )


    page.fill(
        'input[placeholder="Contraseña"]',
        KRIKOS_PASSWORD,
    )


    page.click(
        "#loginButton"
    )


    page.wait_for_selector(
        "#boton-nuevo-documento",
        timeout=20000,
    )


    bloquear_chat(
        page
    )


    # Guardamos el estado de sesión.
    # Si falla, no frenamos el proceso.

    try:

        os.makedirs(
            CARPETA_DATA,
            exist_ok=True,
        )


        page.context.storage_state(
            path=ARCHIVO_ESTADO_SESION
        )

    except Exception:
        pass