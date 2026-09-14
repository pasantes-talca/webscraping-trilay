from pathlib import Path
import os
import time

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.ie.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

IEDRIVER_PATH = (
    BASE_DIR
    / "drivers"
    / "IEDriverServer.exe"
)

EDGE_PATH = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
)

LOG_PATH = BASE_DIR / "iedriver.log"

TRILAY_URL = (
    "http://sistemas.talca.net/trilay/"
)


# =========================================================
# FILTRO
# =========================================================

# Por ahora estamos probando con esta fecha.
# Más adelante podemos hacer que use automáticamente
# la fecha actual o que la pases por consola.

FECHA_BUSQUEDA = "10/09/2026"

CLIENTE = "atomo"


# =========================================================
# CREDENCIALES
# =========================================================

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
        "en el archivo .env"
    )


# =========================================================
# CONFIGURAR EDGE + IE MODE
# =========================================================

options = webdriver.IeOptions()

options.attach_to_edge_chrome = True

options.edge_executable_path = (
    EDGE_PATH
)

options.page_load_strategy = "none"

# Importante:
# iniciar directamente en Trilay evita el problema
# que tuvimos con Protected Mode.
options.initial_browser_url = (
    TRILAY_URL
)


service = Service(
    executable_path=str(
        IEDRIVER_PATH
    ),
    log_output=str(
        LOG_PATH
    ),
    log_level="TRACE"
)


driver = webdriver.Ie(
    service=service,
    options=options
)


try:

    print()
    print("==========================================")
    print(" TRILAY - FACTURAS ATOMO")
    print("==========================================")
    print()

    print(
        "Fecha:",
        FECHA_BUSQUEDA
    )

    print(
        "Cliente:",
        CLIENTE.upper()
    )


    # =====================================================
    # 1. LOGIN
    # =====================================================

    print()
    print(
        "Iniciando sesión..."
    )


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


    print(
        "LOGIN CORRECTO."
    )


    time.sleep(3)


    # =====================================================
    # 2. SELECCIONAR MENDOZA
    # =====================================================

    print()
    print(
        "Seleccionando MENDOZA..."
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


    resultado_mendoza = (
        driver.execute_script(
            """
            var selector =
                document.getElementById(
                    'numCodJerarquia'
                );

            if (!selector) {
                return 'NO_ENCONTRADO';
            }

            selector.value = '7';

            cargarDivs();

            return selector.value;
            """
        )
    )


    if resultado_mendoza != "7":

        raise Exception(
            "No se pudo seleccionar MENDOZA."
        )


    print(
        "MENDOZA seleccionada correctamente."
    )


    time.sleep(5)


    # =====================================================
    # 3. ABRIR VENTAS
    # =====================================================

    print()
    print(
        "Abriendo VENTAS..."
    )


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


    print(
        "VENTAS abierto."
    )


    time.sleep(6)


    # =====================================================
    # 4. ENTRAR AL IFRAME DE VENTAS
    # =====================================================

    print()
    print(
        "Entrando al iframe de Ventas..."
    )


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


    print(
        "Iframe de Ventas correcto."
    )


    time.sleep(3)


    # =====================================================
    # 5. LOCALIZAR LOS CAMPOS REALES
    # =====================================================

    print()
    print(
        "Localizando los campos reales de fecha..."
    )


    resultado_campos = driver.execute_script(
        """
        var fechaDeseada =
            arguments[0];

        var clienteDeseado =
            arguments[1];


        var inputs =
            document.getElementsByTagName(
                'input'
            );


        var visibles =
            [];


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


        // =========================================
        // BUSCAR EL CAMPO DEL CLIENTE
        // =========================================

        var buscador =
            null;

        var infoBuscador =
            null;

        var mayorX =
            -999999;


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


        // =========================================
        // BUSCAR FECHAS A LA IZQUIERDA
        // DEL CAMPO CLIENTE
        // =========================================

        var candidatasFecha =
            [];


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


        // Las ordenamos desde la más cercana
        // al buscador hacia la izquierda.

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
            fechaDeseada
        );


        asignarFecha(
            fechaHasta,
            fechaDeseada
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


        // Guardamos las referencias.
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
        FECHA_BUSQUEDA,
        CLIENTE
    )


    if not resultado_campos.get(
        "ok"
    ):

        print(
            resultado_campos
        )

        raise Exception(
            "No se pudieron localizar "
            "los campos del filtro."
        )


    print()
    print(
        "Campos modificados:"
    )

    print(
        "DESDE:",
        resultado_campos[
            "fechaDesde"
        ]
    )

    print(
        "HASTA:",
        resultado_campos[
            "fechaHasta"
        ]
    )

    print(
        "CLIENTE:",
        resultado_campos[
            "cliente"
        ]
    )


    time.sleep(3)


    # =====================================================
    # 6. VERIFICAR VISUALMENTE LOS FILTROS
    # =====================================================

    print()
    print(
        "Verificando visualmente las fechas..."
    )


    verificacion_campos = (
        driver.execute_script(
            """
            var desde =
                window._trilayFechaDesde;

            var hasta =
                window._trilayFechaHasta;

            var buscador =
                window._trilayBuscador;


            if (
                !desde ||
                !hasta ||
                !buscador
            ) {

                return {
                    ok: false
                };
            }


            return {

                ok:
                    true,

                desde:
                    desde.value,

                hasta:
                    hasta.value,

                cliente:
                    buscador.value
            };
            """
        )
    )


    if not verificacion_campos.get(
        "ok"
    ):

        raise Exception(
            "No se pudieron verificar "
            "los filtros."
        )


    print()
    print(
        "VALOR VISUAL DESDE:",
        verificacion_campos[
            "desde"
        ]
    )

    print(
        "VALOR VISUAL HASTA:",
        verificacion_campos[
            "hasta"
        ]
    )

    print(
        "VALOR VISUAL CLIENTE:",
        verificacion_campos[
            "cliente"
        ]
    )


    if (
        verificacion_campos[
            "desde"
        ]
        != FECHA_BUSQUEDA
    ):

        raise Exception(
            "La fecha DESDE "
            "no quedó correctamente."
        )


    if (
        verificacion_campos[
            "hasta"
        ]
        != FECHA_BUSQUEDA
    ):

        raise Exception(
            "La fecha HASTA "
            "no quedó correctamente."
        )


    if (
        verificacion_campos[
            "cliente"
        ].lower()
        != CLIENTE.lower()
    ):

        raise Exception(
            "El cliente ATOMO "
            "no quedó correctamente."
        )


    print()
    print("==========================================")
    print(" FILTROS VERIFICADOS CORRECTAMENTE")
    print("==========================================")
    print()

    print(
        "DESDE:",
        FECHA_BUSQUEDA
    )

    print(
        "HASTA:",
        FECHA_BUSQUEDA
    )

    print(
        "CLIENTE:",
        CLIENTE.upper()
    )


    # =====================================================
    # 7. EJECUTAR BÚSQUEDA REAL
    # =====================================================

    print()
    print(
        "Ejecutando refreshlistadocoti()..."
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


    print(
        "Resultado búsqueda:",
        resultado_busqueda
    )


    if (
        resultado_busqueda
        == "NO_FUNCION"
    ):

        raise Exception(
            "No se pudo ejecutar "
            "la búsqueda."
        )


    print(
        "Esperando resultados..."
    )

    time.sleep(8)


    # =====================================================
    # 8. BUSCAR EL LISTADO FILTRADO
    # =====================================================

    print()
    print(
        "Buscando listado filtrado..."
    )


    listado_encontrado = (
        False
    )

    cantidad_facturas = (
        0
    )


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

            listado_encontrado = (
                True
            )

    except Exception:
        pass


    # Si no está en el documento actual,
    # buscar dentro de iframes internos.

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

                    listado_encontrado = (
                        True
                    )

                    break


                driver.switch_to.parent_frame()


            except Exception:

                try:
                    driver.switch_to.parent_frame()

                except Exception:
                    pass


    if not listado_encontrado:

        raise Exception(
            "No se encontró el listado "
            "de facturas."
        )


    print(
        "Facturas encontradas:",
        cantidad_facturas
    )


    # =====================================================
    # 9. VERIFICAR FACTURAS RESULTANTES
    # =====================================================

    print()
    print(
        "Verificando las facturas "
        "devueltas por Trilay..."
    )


    verificacion_resultados = (
        driver.execute_script(
            """
            var fechaEsperada =
                arguments[0];

            var clienteEsperado =
                arguments[1]
                .toUpperCase();


            var checks =
                document.getElementsByName(
                    'chkborrar'
                );


            var correctas =
                0;

            var incorrectas =
                0;


            for (
                var i = 0;
                i < checks.length;
                i++
            ) {

                var check =
                    checks[i];


                var fecha =
                    check.getAttribute(
                        'artfechacomprobante'
                    ) || '';


                var fila =
                    check;


                while (
                    fila &&
                    fila.tagName != 'TR'
                ) {

                    fila =
                        fila.parentNode;
                }


                var textoFila =
                    '';


                if (fila) {

                    textoFila =
                        (
                            fila.innerText ||
                            fila.textContent ||
                            ''
                        ).toUpperCase();
                }


                var fechaOK =
                    fecha
                    == fechaEsperada;


                var clienteOK =
                    textoFila.indexOf(
                        clienteEsperado
                    ) >= 0;


                if (
                    fechaOK &&
                    clienteOK
                ) {

                    correctas++;

                } else {

                    incorrectas++;
                }
            }


            return {

                total:
                    checks.length,

                correctas:
                    correctas,

                incorrectas:
                    incorrectas
            };
            """,
            FECHA_BUSQUEDA,
            "ATOMO"
        )
    )


    print()
    print(
        "TOTAL:",
        verificacion_resultados[
            "total"
        ]
    )

    print(
        "CORRECTAS:",
        verificacion_resultados[
            "correctas"
        ]
    )

    print(
        "INCORRECTAS:",
        verificacion_resultados[
            "incorrectas"
        ]
    )


    if (
        verificacion_resultados[
            "total"
        ]
        == 0
    ):

        raise Exception(
            "No se encontraron facturas."
        )


    if (
        verificacion_resultados[
            "incorrectas"
        ]
        > 0
    ):

        raise Exception(
            "El filtro devolvió facturas "
            "incorrectas. "
            "Se cancela la impresión."
        )


    print()
    print("==========================================")
    print(" FILTRO APLICADO CORRECTAMENTE")
    print("==========================================")
    print()

    print(
        "Todas las facturas son de "
        "ATOMO y del",
        FECHA_BUSQUEDA
    )

    print()
    print(
        "Cantidad:",
        verificacion_resultados[
            "correctas"
        ]
    )


    # =====================================================
    # 10. SELECCIONAR TODAS
    # =====================================================

    print()
    print(
        "Seleccionando todas las "
        "facturas filtradas..."
    )


    resultado_seleccion = (
        driver.execute_script(
            """
            if (
                typeof seleccionar
                === 'function'
            ) {

                seleccionar(true);

                return 'FUNCION_SELECCIONAR';
            }


            var checks =
                document.getElementsByName(
                    'chkborrar'
                );


            for (
                var i = 0;
                i < checks.length;
                i++
            ) {

                checks[i].checked =
                    true;
            }


            return 'SELECCION_DIRECTA';
            """
        )
    )


    print(
        "Método de selección:",
        resultado_seleccion
    )


    cantidad_seleccionadas = (
        driver.execute_script(
            """
            var checks =
                document.getElementsByName(
                    'chkborrar'
                );

            var cantidad =
                0;


            for (
                var i = 0;
                i < checks.length;
                i++
            ) {

                if (
                    checks[i].checked
                ) {

                    cantidad++;
                }
            }


            return cantidad;
            """
        )
    )


    print(
        "Facturas seleccionadas:",
        cantidad_seleccionadas
    )


    if (
        cantidad_seleccionadas
        !=
        verificacion_resultados[
            "correctas"
        ]
    ):

        raise Exception(
            "No se seleccionaron todas "
            "las facturas."
        )


    print(
        "Todas las facturas fueron "
        "seleccionadas correctamente."
    )


    time.sleep(2)


    # =====================================================
    # 11. OBTENER CÓDIGOS DE FACTURA
    # =====================================================

    print()
    print(
        "Preparando impresión múltiple..."
    )


    codigos_facturas = (
        driver.execute_script(
            """
            var checks =
                document.getElementsByName(
                    'chkborrar'
                );


            var codigos =
                [];


            for (
                var i = 0;
                i < checks.length;
                i++
            ) {

                if (
                    checks[i].checked
                ) {

                    codigos.push(
                        checks[i].value
                    );
                }
            }


            return codigos;
            """
        )
    )


    if not codigos_facturas:

        raise Exception(
            "No hay facturas "
            "seleccionadas."
        )


    print(
        "Facturas para imprimir:",
        len(codigos_facturas)
    )


    cadena_codigos = (
        "|".join(
            codigos_facturas
        )
    )


    print(
        "Códigos preparados correctamente."
    )


    # =====================================================
    # 12. ABRIR IMPRESIÓN MÚLTIPLE DIRECTAMENTE
    # =====================================================

    print()
    print(
        "Abriendo directamente "
        "Imprimir Múltiples Facturas..."
    )


    url_impresion = (
        "ImprimirMultiplesFacturas.asp"
        "?accion=INICIO"
        "&CodJerarquia=7"
        "&codi="
        + cadena_codigos
    )


    print(
        "Página de impresión preparada."
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


    print(
        "Módulo de impresión abierto."
    )


    time.sleep(6)


    # =====================================================
    # 13. ENTRAR AL IFRAME MOTOR
    # =====================================================

    print()
    print(
        "Entrando al módulo de impresión..."
    )


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


    print(
        "Módulo de impresión cargado."
    )


    time.sleep(5)


    # =====================================================
    # 14. ESPERAR LISTA DE IMPRESORAS
    # =====================================================

    print()
    print(
        "Esperando lista de impresoras..."
    )


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


    print(
        "Lista de impresoras cargada."
    )


    # =====================================================
    # 15. SELECCIONAR PDF
    # =====================================================

    print()
    print(
        "Seleccionando PDF..."
    )


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


    print(
        "Valor seleccionado:",
        resultado_pdf
    )


    if resultado_pdf != "PDF":

        raise Exception(
            "No se pudo seleccionar PDF."
        )


    print(
        "PDF seleccionado correctamente."
    )


    # =====================================================
    # 16. VERIFICAR PDF
    # =====================================================

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


    print(
        "Impresora seleccionada:",
        impresora_actual
    )


    if impresora_actual != "PDF":

        raise Exception(
            "La impresora seleccionada "
            "no es PDF."
        )


    time.sleep(2)


    # =====================================================
    # 17. BOTÓN IMPRIMIR
    # =====================================================

    print()
    print(
        "Buscando botón IMPRIMIR..."
    )


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


    print(
        "Botón IMPRIMIR encontrado."
    )


    # =====================================================
    # 18. HACER CLIC EN IMPRIMIR
    # =====================================================

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


    print()
    print("==========================================")
    print(" IMPRESIÓN PDF INICIADA")
    print("==========================================")
    print()

    print(
        "Fecha:",
        FECHA_BUSQUEDA
    )

    print(
        "Cliente:",
        CLIENTE.upper()
    )

    print(
        "Facturas:",
        len(codigos_facturas)
    )

    print(
        "Impresora:",
        "PDF"
    )


    # =====================================================
    # 19. ESPERAR PROCESAMIENTO DE TODAS LAS FACTURAS
    # =====================================================

    print()
    print(
        "Esperando procesamiento "
        "de las facturas..."
    )


    try:

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


        print()
        print(
            "Todas las facturas fueron procesadas."
        )


    except Exception:

        # Esto NO lo tomamos como error general porque
        # la impresión ya fue iniciada.
        print()
        print(
            "La impresión fue iniciada, "
            "pero no se pudo confirmar "
            "automáticamente el contador final."
        )


    # =====================================================
    # 20. RESUMEN FINAL
    # =====================================================

    print()
    print("==========================================")
    print(" PROCESO COMPLETADO")
    print("==========================================")
    print()

    print(
        "Fecha:",
        FECHA_BUSQUEDA
    )

    print(
        "Cliente:",
        CLIENTE.upper()
    )

    print(
        "Facturas enviadas a PDF:",
        len(codigos_facturas)
    )

    print()
    print(
        "Trilay terminó el proceso de "
        "impresión múltiple."
    )


# =========================================================
# ERROR GENERAL
# =========================================================

except Exception as error:

    print()
    print("==========================================")
    print(" ERROR DURANTE LA AUTOMATIZACIÓN")
    print("==========================================")
    print()

    print(
        type(error).__name__
    )

    print(
        error
    )


# =========================================================
# MANTENER EL NAVEGADOR ABIERTO
# =========================================================

input(
    "\nPresioná ENTER para cerrar..."
)


try:

    driver.quit()

except Exception:

    pass