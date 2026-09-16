from pathlib import Path
from datetime import datetime
import os
import time
import shutil

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

# Usa automáticamente la fecha actual de la PC
# tanto en DESDE como en HASTA.

FECHA_DESDE = datetime.now().strftime("%d/%m/%Y")
FECHA_HASTA = datetime.now().strftime("%d/%m/%Y")

CLIENTE = "atomo"


# =========================================================
# CARPETA DE FACTURAS
# =========================================================

# Trilay genera los PDF inicialmente en esta carpeta de red.
CARPETA_FACTURAS = Path(r"\\192.168.10.3\Facturas Jumbo")

# Ejemplo: 16-09-2026
# Se usan guiones porque Windows no permite / en nombres de carpetas.
NOMBRE_CARPETA_HOY = datetime.now().strftime("%d-%m-%Y")

CARPETA_FACTURAS_HOY = (
    CARPETA_FACTURAS
    / NOMBRE_CARPETA_HOY
)


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

# IMPORTANTE:
# Iniciar directamente en Trilay evita
# el problema con Protected Mode.

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
        "Desde:",
        FECHA_DESDE
    )

    print(
        "Hasta:",
        FECHA_HASTA
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
    # 5. LOCALIZAR CAMPOS DE FECHA Y CLIENTE
    # =====================================================

    print()
    print(
        "Localizando los campos reales de fecha..."
    )


    resultado_campos = driver.execute_script(
        """
        var fechaDesdeDeseada = arguments[0];
        var fechaHastaDeseada = arguments[1];
        var clienteDeseado = arguments[2];


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


        // =========================================
        // BUSCAR CAMPO CLIENTE
        // =========================================

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


        // =========================================
        // BUSCAR LAS DOS FECHAS
        // =========================================

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
        FECHA_DESDE,
        FECHA_HASTA,
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
    # 6. VERIFICAR FILTROS
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
        != FECHA_DESDE
    ):

        raise Exception(
            "La fecha DESDE "
            "no quedó correctamente."
        )


    if (
        verificacion_campos[
            "hasta"
        ]
        != FECHA_HASTA
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
        FECHA_DESDE
    )


    print(
        "HASTA:",
        FECHA_HASTA
    )


    print(
        "CLIENTE:",
        CLIENTE.upper()
    )


    # =====================================================
    # 7. EJECUTAR BÚSQUEDA
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
    # 8. BUSCAR LISTADO FILTRADO
    # =====================================================

    print()
    print(
        "Buscando listado filtrado..."
    )


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

        raise Exception(
            "No se encontró el listado "
            "de facturas."
        )


    print(
        "Facturas encontradas:",
        cantidad_facturas
    )


    # =====================================================
    # 9. VERIFICAR FACTURAS DEL RANGO
    # =====================================================

    print()
    print(
        "Verificando las facturas "
        "devueltas por Trilay..."
    )


    verificacion_resultados = (
        driver.execute_script(
            """
            var fechaDesdeTexto =
                arguments[0];

            var fechaHastaTexto =
                arguments[1];

            var clienteEsperado =
                arguments[2]
                .toUpperCase();


            function convertirFecha(
                texto
            ) {

                if (!texto) {
                    return null;
                }


                var partes =
                    texto.split('/');


                if (
                    partes.length != 3
                ) {
                    return null;
                }


                var dia =
                    parseInt(
                        partes[0],
                        10
                    );


                var mes =
                    parseInt(
                        partes[1],
                        10
                    );


                var anio =
                    parseInt(
                        partes[2],
                        10
                    );


                return new Date(
                    anio,
                    mes - 1,
                    dia
                );
            }


            var fechaDesde =
                convertirFecha(
                    fechaDesdeTexto
                );


            var fechaHasta =
                convertirFecha(
                    fechaHastaTexto
                );


            var checks =
                document.getElementsByName(
                    'chkborrar'
                );


            var correctas = 0;

            var incorrectas = 0;


            for (
                var i = 0;
                i < checks.length;
                i++
            ) {

                var check =
                    checks[i];


                var fechaTexto =
                    check.getAttribute(
                        'artfechacomprobante'
                    ) || '';


                var fechaFactura =
                    convertirFecha(
                        fechaTexto
                    );


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
                        ).toUpperCase();
                }


                var fechaOK = false;


                if (
                    fechaFactura &&
                    fechaDesde &&
                    fechaHasta
                ) {

                    fechaOK =
                        fechaFactura >= fechaDesde
                        &&
                        fechaFactura <= fechaHasta;
                }


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
            FECHA_DESDE,
            FECHA_HASTA,
            CLIENTE
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
            "fuera del rango o de otro cliente. "
            "Se cancela la impresión."
        )


    print()
    print("==========================================")
    print(" FILTRO APLICADO CORRECTAMENTE")
    print("==========================================")
    print()


    print(
        "Todas las facturas son de ATOMO"
    )


    print(
        "y están dentro del rango:"
    )


    print(
        FECHA_DESDE,
        "hasta",
        FECHA_HASTA
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

            var cantidad = 0;


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
    # 11. OBTENER CÓDIGOS
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


            var codigos = [];


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
    # 12. ABRIR IMPRESIÓN MÚLTIPLE
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
    # 18. REGISTRAR PDF EXISTENTES ANTES DE IMPRIMIR
    # =====================================================

    print()
    print(
        "Registrando los PDF que ya existen "
        "en la carpeta de red..."
    )

    if not CARPETA_FACTURAS.exists():

        raise Exception(
            "No se puede acceder a la carpeta de red: "
            f"{CARPETA_FACTURAS}"
        )


    pdf_antes = {}

    for archivo in CARPETA_FACTURAS.glob(
        "*.pdf"
    ):

        try:

            datos = archivo.stat()

            pdf_antes[archivo.name] = (
                datos.st_mtime_ns,
                datos.st_size
            )

        except Exception:
            pass


    print(
        "PDF existentes antes de imprimir:",
        len(pdf_antes)
    )


    # =====================================================
    # 19. HACER CLIC EN IMPRIMIR
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
        "Desde:",
        FECHA_DESDE
    )


    print(
        "Hasta:",
        FECHA_HASTA
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
    # 20. ESPERAR PROCESAMIENTO
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

        print()
        print(
            "La impresión fue iniciada, "
            "pero no se pudo confirmar "
            "automáticamente el contador final."
        )


    # =====================================================
    # 21. CREAR CARPETA DEL DÍA Y MOVER LOS PDF GENERADOS
    # =====================================================

    print()
    print("==========================================")
    print(" ORGANIZANDO FACTURAS")
    print("==========================================")
    print()

    CARPETA_FACTURAS_HOY.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "Carpeta del día:",
        CARPETA_FACTURAS_HOY
    )

    print()
    print(
        "Esperando que los PDF generados aparezcan "
        "en la carpeta de red..."
    )


    def buscar_pdfs_generados():

        encontrados = []

        for archivo in CARPETA_FACTURAS.glob(
            "*.pdf"
        ):

            try:

                datos = archivo.stat()

                estado_anterior = pdf_antes.get(
                    archivo.name
                )

                estado_actual = (
                    datos.st_mtime_ns,
                    datos.st_size
                )

                # Es nuevo o fue regenerado/modificado
                # durante esta ejecución.
                if (
                    estado_anterior is None
                    or estado_actual != estado_anterior
                ):

                    encontrados.append(
                        archivo
                    )

            except Exception:
                pass

        return encontrados


    # Damos hasta 90 segundos para que la carpeta de red
    # refleje todos los PDF generados por Trilay.
    limite_espera = time.time() + 90

    pdf_generados = []

    while time.time() < limite_espera:

        pdf_generados = buscar_pdfs_generados()

        print(
            "PDF detectados:",
            len(pdf_generados),
            "de",
            len(codigos_facturas)
        )

        if (
            len(pdf_generados)
            >= len(codigos_facturas)
        ):
            break

        time.sleep(2)


    if not pdf_generados:

        raise Exception(
            "Trilay terminó la impresión, pero no se "
            "detectaron PDF nuevos o modificados en "
            f"{CARPETA_FACTURAS}"
        )


    # Esperar a que cada PDF termine de escribirse.
    # Comparamos el tamaño dos veces antes de moverlo.
    print()
    print(
        "Verificando que los PDF hayan terminado "
        "de escribirse..."
    )

    pdf_estables = []

    for pdf in pdf_generados:

        estable = False

        for intento in range(10):

            try:

                tamano_1 = pdf.stat().st_size

                time.sleep(1)

                tamano_2 = pdf.stat().st_size

                if (
                    tamano_1 > 0
                    and tamano_1 == tamano_2
                ):

                    estable = True
                    break

            except Exception:
                pass

        if estable:

            pdf_estables.append(
                pdf
            )

        else:

            print(
                "No se pudo confirmar que terminó de "
                "escribirse:",
                pdf.name
            )


    print()
    print(
        "PDF listos para mover:",
        len(pdf_estables)
    )


    pdf_movidos = 0
    pdf_reemplazados = 0
    errores_moviendo = 0

    for pdf in pdf_estables:

        destino = (
            CARPETA_FACTURAS_HOY
            / pdf.name
        )

        try:

            # Si el proceso se ejecutó nuevamente el mismo día
            # y el archivo ya existe, conservamos una sola copia:
            # reemplazamos la anterior por la recién generada.
            if destino.exists():

                destino.unlink()

                pdf_reemplazados += 1

            shutil.move(
                str(pdf),
                str(destino)
            )

            print(
                "Movido:",
                pdf.name
            )

            pdf_movidos += 1

        except Exception as error_archivo:

            errores_moviendo += 1

            print(
                "No se pudo mover:",
                pdf.name
            )

            print(
                error_archivo
            )


    print()
    print("==========================================")
    print(" FACTURAS ORGANIZADAS")
    print("==========================================")
    print()

    print(
        "Carpeta:",
        CARPETA_FACTURAS_HOY
    )

    print(
        "PDF movidos:",
        pdf_movidos
    )

    print(
        "PDF reemplazados por una versión nueva:",
        pdf_reemplazados
    )

    print(
        "Errores al mover:",
        errores_moviendo
    )


    # =====================================================
    # 22. RESUMEN FINAL
    # =====================================================

    print()
    print("==========================================")
    print(" PROCESO COMPLETADO")
    print("==========================================")
    print()


    print(
        "Desde:",
        FECHA_DESDE
    )


    print(
        "Hasta:",
        FECHA_HASTA
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
# MANTENER NAVEGADOR ABIERTO
# =========================================================

input(
    "\nPresioná ENTER para cerrar..."
)


try:

    driver.quit()

except Exception:

    pass