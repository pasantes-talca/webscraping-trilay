import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import SUCURSALES


def imprimir_facturas_pdf(
    driver,
    facturas,
    sucursal,
):

    if not facturas:
        raise ValueError(
            "No hay facturas para imprimir."
        )


    codigo_sucursal = SUCURSALES.get(
        sucursal
    )


    if not codigo_sucursal:
        raise ValueError(
            f"Sucursal no configurada: {sucursal}"
        )


    # ==========================================
    # OBTENER CÓDIGOS
    # ==========================================

    codigos_facturas = [
        factura["codigo"]
        for factura in facturas
    ]


    cadena_codigos = "|".join(
        codigos_facturas
    )


    # ==========================================
    # ABRIR IMPRESIÓN MÚLTIPLE
    # ==========================================

    url_impresion = (
        "ImprimirMultiplesFacturas.asp"
        "?accion=INICIO"
        f"&CodJerarquia={codigo_sucursal}"
        "&codi="
        + cadena_codigos
    )


    resultado_motor = (
        driver.execute_script(
            """
            var url =
                arguments[0];


            var contenedor =
                document.getElementById(
                    'ImpresionMultiple'
                );


            if (!contenedor) {

                return 'NO_CONTENEDOR';
            }


            contenedor.style.display =
                'block';


            var motor =
                document.getElementById(
                    'motor'
                );


            if (!motor) {

                motor =
                    document.createElement(
                        'iframe'
                    );


                motor.id =
                    'motor';

                motor.name =
                    'motor';

                motor.style.width =
                    '550px';

                motor.style.height =
                    '300px';

                motor.style.display =
                    'block';


                contenedor.innerHTML =
                    '';


                contenedor.appendChild(
                    motor
                );
            }


            motor.src =
                url;


            return 'OK';
            """,
            url_impresion
        )
    )


    if resultado_motor != "OK":

        raise Exception(
            "No se pudo abrir "
            "el módulo de impresión."
        )


    time.sleep(6)


    # ==========================================
    # ENTRAR AL IFRAME MOTOR
    # ==========================================

    iframe_motor = (
        WebDriverWait(
            driver,
            30
        ).until(
            EC.presence_of_element_located(
                (
                    By.ID,
                    "motor"
                )
            )
        )
    )


    driver.switch_to.frame(
        iframe_motor
    )


    time.sleep(5)


    # ==========================================
    # ESPERAR LISTA DE IMPRESORAS
    # ==========================================

    WebDriverWait(
        driver,
        30
    ).until(
        EC.presence_of_element_located(
            (
                By.ID,
                "cboImpresoras"
            )
        )
    )


    # ==========================================
    # SELECCIONAR PDF
    # ==========================================

    resultado_pdf = (
        driver.execute_script(
            """
            var selector =
                document.getElementById(
                    'cboImpresoras'
                );


            if (!selector) {

                return 'NO_SELECTOR';
            }


            selector.value =
                'PDF';


            try {

                if (
                    selector.fireEvent
                ) {

                    selector.fireEvent(
                        'onchange'
                    );
                }

            } catch(e) {}


            return selector.value;
            """
        )
    )


    if resultado_pdf != "PDF":

        raise Exception(
            "No se pudo seleccionar PDF."
        )


    # ==========================================
    # VERIFICAR PDF
    # ==========================================

    impresora_actual = (
        driver.execute_script(
            """
            var selector =
                document.getElementById(
                    'cboImpresoras'
                );


            if (!selector) {

                return '';
            }


            return selector.value;
            """
        )
    )


    if impresora_actual != "PDF":

        raise Exception(
            "La impresora seleccionada "
            "no es PDF."
        )


    time.sleep(2)


    # ==========================================
    # BOTÓN IMPRIMIR
    # ==========================================

    WebDriverWait(
        driver,
        30
    ).until(
        EC.presence_of_element_located(
            (
                By.ID,
                "btComenzar"
            )
        )
    )


    resultado_imprimir = (
        driver.execute_script(
            """
            var boton =
                document.getElementById(
                    'btComenzar'
                );


            if (!boton) {

                return false;
            }


            boton.click();


            return true;
            """
        )
    )


    if not resultado_imprimir:

        raise Exception(
            "No se pudo presionar Imprimir."
        )


    # ==========================================
    # ESPERAR PROCESAMIENTO
    # ==========================================

    WebDriverWait(
        driver,
        120
    ).until(
        lambda navegador:

            int(
                navegador.execute_script(
                    """
                    var contador =
                        document.getElementById(
                            'porcentajeprocesado'
                        );


                    if (!contador) {
                        return '0';
                    }


                    return (
                        contador.innerHTML
                        || '0'
                    );
                    """
                )
                or "0"
            )
            >=
            len(codigos_facturas)
    )