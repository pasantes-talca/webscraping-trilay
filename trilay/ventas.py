import time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import SUCURSALES


def seleccionar_sucursal(driver, sucursal):

    codigo_sucursal = SUCURSALES.get(
        sucursal
    )

    if not codigo_sucursal:

        raise ValueError(
            f"Sucursal no configurada: {sucursal}"
        )


    WebDriverWait(
        driver,
        30
    ).until(
        EC.presence_of_element_located(
            (
                By.ID,
                "numCodJerarquia"
            )
        )
    )


    resultado = driver.execute_script(
        """
        var selector =
            document.getElementById(
                'numCodJerarquia'
            );

        if (!selector) {
            return 'NO_ENCONTRADO';
        }

        selector.value =
            arguments[0];

        cargarDivs();

        return selector.value;
        """,
        codigo_sucursal
    )


    if resultado != codigo_sucursal:

        raise Exception(
            f"No se pudo seleccionar {sucursal}."
        )


    time.sleep(5)


def abrir_ventas(driver):

    bloque_ventas = (
        WebDriverWait(
            driver,
            30
        ).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[@id='trilay-escritorio']"
                    "//*[normalize-space(text())='Ventas']"
                )
            )
        )
    )


    driver.execute_script(
        "arguments[0].click();",
        bloque_ventas
    )


    time.sleep(6)


    iframe_ventas = (
        WebDriverWait(
            driver,
            30
        ).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//iframe[contains("
                    "@src,"
                    "'ventas/ventas.asp'"
                    ")]"
                )
            )
        )
    )


    driver.switch_to.frame(
        iframe_ventas
    )


    time.sleep(3)


def aplicar_filtros(
    driver,
    fecha_desde,
    fecha_hasta,
    cliente,
):

    resultado_campos = driver.execute_script(
        """
        var fechaDesdeDeseada =
            arguments[0];

        var fechaHastaDeseada =
            arguments[1];

        var clienteDeseado =
            arguments[2];


        var inputs =
            document.getElementsByTagName(
                'input'
            );


        var visibles = [];


        for (
            var i = 0;
            i < inputs.length;
            i++
        ) {

            var input =
                inputs[i];

            var rect =
                input.getBoundingClientRect();


            if (
                rect.width <= 0 ||
                rect.height <= 0
            ) {
                continue;
            }


            visibles.push({

                elemento:
                    input,

                x:
                    rect.left,

                y:
                    rect.top,

                derecha:
                    rect.right,

                valor:
                    input.value || ''
            });
        }


        if (
            visibles.length == 0
        ) {

            return {
                ok: false,
                error:
                    'NO_INPUTS_VISIBLES'
            };
        }


        var buscador = null;

        var infoBuscador = null;

        var mayorX = -999999;


        for (
            var j = 0;
            j < visibles.length;
            j++
        ) {

            var info =
                visibles[j];

            var valor =
                info.valor;


            if (
                /^\\d{1,2}\\/\\d{1,2}\\/\\d{4}$/
                .test(valor)
            ) {
                continue;
            }


            if (
                info.x > mayorX
            ) {

                mayorX =
                    info.x;

                buscador =
                    info.elemento;

                infoBuscador =
                    info;
            }
        }


        if (!buscador) {

            return {
                ok: false,
                error:
                    'NO_BUSCADOR'
            };
        }


        var candidatasFecha = [];


        for (
            var k = 0;
            k < visibles.length;
            k++
        ) {

            var candidato =
                visibles[k];


            if (
                candidato.elemento
                == buscador
            ) {
                continue;
            }


            var mismaFila =
                Math.abs(
                    candidato.y -
                    infoBuscador.y
                ) <= 12;


            var izquierda =
                candidato.derecha
                <=
                infoBuscador.x + 5;


            if (
                !mismaFila ||
                !izquierda
            ) {
                continue;
            }


            if (
                /^\\d{1,2}\\/\\d{1,2}\\/\\d{4}$/
                .test(
                    candidato.valor
                )
            ) {

                candidatasFecha.push(
                    candidato
                );
            }
        }


        if (
            candidatasFecha.length < 2
        ) {

            return {
                ok: false,
                error:
                    'NO_DOS_FECHAS',
                cantidad:
                    candidatasFecha.length
            };
        }


        candidatasFecha.sort(
            function(a, b) {
                return b.x - a.x;
            }
        );


        var fechaHasta =
            candidatasFecha[0]
            .elemento;


        var fechaDesde =
            candidatasFecha[1]
            .elemento;


        function asignarFecha(
            campo,
            valor
        ) {

            try {
                campo.focus();
            } catch(e) {}


            campo.value =
                valor;


            try {

                if (
                    campo.fireEvent
                ) {

                    campo.fireEvent(
                        'onchange'
                    );

                    campo.fireEvent(
                        'onblur'
                    );

                    campo.fireEvent(
                        'onkeyup'
                    );
                }

            } catch(e) {}


            try {
                campo.blur();
            } catch(e) {}
        }


        asignarFecha(
            fechaDesde,
            fechaDesdeDeseada
        );


        asignarFecha(
            fechaHasta,
            fechaHastaDeseada
        );


        buscador.value =
            clienteDeseado;


        try {

            if (
                buscador.fireEvent
            ) {

                buscador.fireEvent(
                    'onchange'
                );

                buscador.fireEvent(
                    'onkeyup'
                );
            }

        } catch(e) {}


        window._trilayFechaDesde =
            fechaDesde;

        window._trilayFechaHasta =
            fechaHasta;

        window._trilayBuscador =
            buscador;


        return {

            ok:
                true,

            fechaDesde:
                fechaDesde.value,

            fechaHasta:
                fechaHasta.value,

            cliente:
                buscador.value
        };
        """,
        fecha_desde,
        fecha_hasta,
        cliente
    )


    if not resultado_campos.get(
        "ok"
    ):

        raise Exception(
            "No se pudieron localizar "
            "los campos del filtro."
        )


    if (
        resultado_campos[
            "fechaDesde"
        ]
        != fecha_desde
    ):

        raise Exception(
            "La fecha DESDE "
            "no quedó correctamente."
        )


    if (
        resultado_campos[
            "fechaHasta"
        ]
        != fecha_hasta
    ):

        raise Exception(
            "La fecha HASTA "
            "no quedó correctamente."
        )


    if (
        resultado_campos[
            "cliente"
        ].lower()
        != cliente.lower()
    ):

        raise Exception(
            "El cliente "
            "no quedó correctamente."
        )


    resultado_busqueda = (
        driver.execute_script(
            """
            if (
                typeof refreshlistadocoti
                === 'function'
            ) {

                refreshlistadocoti();

                return 'REFRESH_LOCAL';
            }


            try {

                if (
                    parent &&
                    typeof parent.refreshlistadocoti
                    === 'function'
                ) {

                    parent.refreshlistadocoti();

                    return 'REFRESH_PARENT';
                }

            } catch(e) {}


            return 'NO_FUNCION';
            """
        )
    )


    if (
        resultado_busqueda
        == "NO_FUNCION"
    ):

        raise Exception(
            "No se pudo ejecutar "
            "la búsqueda."
        )


    time.sleep(8)


def obtener_facturas(
    driver,
    fecha_desde,
    fecha_hasta,
    cliente,
):

    listado_encontrado = False


    cantidad_facturas = 0


    try:

        cantidad_facturas = (
            driver.execute_script(
                """
                return document
                    .getElementsByName(
                        'chkborrar'
                    ).length;
                """
            )
        )


        if (
            cantidad_facturas > 0
        ):

            listado_encontrado = True


    except Exception:
        pass


    if not listado_encontrado:

        frames = (
            driver.find_elements(
                By.TAG_NAME,
                "iframe"
            )
        )


        for frame in frames:

            try:

                driver.switch_to.frame(
                    frame
                )


                cantidad_temporal = (
                    driver.execute_script(
                        """
                        return document
                            .getElementsByName(
                                'chkborrar'
                            ).length;
                        """
                    )
                )


                if (
                    cantidad_temporal > 0
                ):

                    cantidad_facturas = (
                        cantidad_temporal
                    )

                    listado_encontrado = True

                    break


                driver.switch_to.parent_frame()


            except Exception:

                try:

                    driver.switch_to.parent_frame()

                except Exception:
                    pass


    if not listado_encontrado:

        return []


    facturas = (
        driver.execute_script(
            """
            var checks =
                document.getElementsByName(
                    'chkborrar'
                );


            var resultado = [];


            for (
                var i = 0;
                i < checks.length;
                i++
            ) {

                var check =
                    checks[i];


                var fila =
                    check;


                while (
                    fila &&
                    fila.tagName != 'TR'
                ) {

                    fila =
                        fila.parentNode;
                }


                var textoFila = '';


                if (fila) {

                    textoFila =
                        (
                            fila.innerText ||
                            fila.textContent ||
                            ''
                        );
                }


                resultado.push({

                    codigo:
                        check.value,

                    fecha:
                        check.getAttribute(
                            'artfechacomprobante'
                        ) || '',

                    texto:
                        textoFila
                });
            }


            return resultado;
            """
        )
    )


    fecha_inicio = datetime.strptime(
        fecha_desde,
        "%d/%m/%Y"
    )


    fecha_fin = datetime.strptime(
        fecha_hasta,
        "%d/%m/%Y"
    )


    facturas_validas = []


    for factura in facturas:

        try:

            fecha_factura = (
                datetime.strptime(
                    factura["fecha"],
                    "%d/%m/%Y"
                )
            )

        except Exception:

            continue


        cliente_ok = (
            cliente.upper()
            in factura[
                "texto"
            ].upper()
        )


        fecha_ok = (
            fecha_inicio
            <= fecha_factura
            <= fecha_fin
        )


        if (
            fecha_ok
            and cliente_ok
        ):

            facturas_validas.append(
                factura
            )


    if (
        len(facturas_validas)
        !=
        len(facturas)
    ):

        raise Exception(
            "El filtro devolvió facturas "
            "fuera del rango o de otro cliente."
        )


    return facturas_validas


def seleccionar_facturas(
    driver,
    facturas,
):

    codigos = {
        factura["codigo"]
        for factura in facturas
    }


    cantidad_seleccionadas = (
        driver.execute_script(
            """
            var codigos =
                arguments[0];


            var checks =
                document.getElementsByName(
                    'chkborrar'
                );


            var seleccionadas = 0;


            for (
                var i = 0;
                i < checks.length;
                i++
            ) {

                var check =
                    checks[i];


                check.checked =
                    codigos.indexOf(
                        check.value
                    ) >= 0;


                if (
                    check.checked
                ) {

                    seleccionadas++;
                }
            }


            return seleccionadas;
            """,
            list(codigos)
        )
    )


    if (
        cantidad_seleccionadas
        != len(facturas)
    ):

        raise Exception(
            "No se pudieron seleccionar "
            "todas las facturas."
        )