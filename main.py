from pathlib import Path
from datetime import datetime
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
    r"C:\Program Files (x86)"
    r"\Microsoft\Edge\Application\msedge.exe"
)

LOG_PATH = BASE_DIR / "iedriver.log"

TRILAY_URL = (
    "http://sistemas.talca.net/trilay/"
)


# Carpeta donde después guardaremos
# los PDF descargados.
DOWNLOADS_DIR = BASE_DIR / "downloads"

DOWNLOADS_DIR.mkdir(
    exist_ok=True
)


# =========================================================
# FECHA Y CLIENTE
# =========================================================

# La fecha se calcula automáticamente
# cada vez que ejecutás el programa.

FECHA_HOY = datetime.now().strftime(
    "%d/%m/%Y"
)

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
        "No se encontraron las "
        "credenciales en el archivo .env"
    )


# =========================================================
# CONFIGURAR EDGE + IE MODE
# =========================================================

print()
print("========================================")
print(" AUTOMATIZACIÓN TRILAY - FACTURAS ATOMO ")
print("========================================")
print()

print(
    "Fecha:",
    FECHA_HOY
)

print(
    "Cliente:",
    CLIENTE.upper()
)

print()


options = webdriver.IeOptions()

options.attach_to_edge_chrome = True

options.edge_executable_path = (
    EDGE_PATH
)

options.page_load_strategy = "none"


# Esto evita el problema de Protected Mode
# que tuvimos al comienzo.
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

    # =====================================================
    # 1. LOGIN AUTOMÁTICO
    # =====================================================

    print(
        "Iniciando Trilay..."
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


    print(
        "Credenciales completadas."
    )


    boton_ingresar = espera.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[normalize-space()='Ingresar']"
            )
        )
    )


    boton_ingresar.click()


    print(
        "Login enviado."
    )

    print(
        "Esperando escritorio..."
    )


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
            "No se pudo seleccionar "
            "MENDOZA."
        )


    print(
        "MENDOZA seleccionada."
    )


    print(
        "Esperando carga de Mendoza..."
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


    print(
        "Esperando grilla..."
    )


    time.sleep(6)


    # =====================================================
    # 4. ENTRAR AL IFRAME DE VENTAS
    # =====================================================

    print()
    print(
        "Buscando iframe de Ventas..."
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
        "Entramos al iframe de Ventas."
    )


    time.sleep(3)


    # =====================================================
    # 5. CONFIGURAR FILTROS
    # =====================================================

    print()
    print(
        "Configurando filtros..."
    )


    resultado_filtros = (
        driver.execute_script(
            """
            var fechaHoy = arguments[0];
            var cliente = arguments[1];

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
                    elemento: input,
                    x: rect.left,
                    valor: input.value || ''
                });

            }


            visibles.sort(
                function(a, b) {
                    return a.x - b.x;
                }
            );


            // -----------------------------
            // IDENTIFICAR FECHAS
            // -----------------------------

            var fechas = [];


            for (
                var j = 0;
                j < visibles.length;
                j++
            ) {

                var valor =
                    visibles[j].valor;


                if (
                    /^\\d{1,2}\\/\\d{1,2}\\/\\d{4}$/
                    .test(valor)
                ) {

                    fechas.push(
                        visibles[j].elemento
                    );

                }

            }


            if (fechas.length < 2) {

                return {
                    ok: false,
                    error: 'NO_FECHAS'
                };

            }


            fechas[0].value =
                fechaHoy;

            fechas[1].value =
                fechaHoy;


            // -----------------------------
            // IDENTIFICAR BUSCADOR
            // -----------------------------

            var buscador = null;

            var mayorX = -1;


            for (
                var k = 0;
                k < visibles.length;
                k++
            ) {

                var campo =
                    visibles[k].elemento;

                var valorCampo =
                    campo.value || '';


                if (
                    /^\\d{1,2}\\/\\d{1,2}\\/\\d{4}$/
                    .test(valorCampo)
                ) {
                    continue;
                }


                if (
                    visibles[k].x > mayorX
                ) {

                    mayorX =
                        visibles[k].x;

                    buscador =
                        campo;

                }

            }


            if (!buscador) {

                return {
                    ok: false,
                    error: 'NO_BUSCADOR'
                };

            }


            buscador.value =
                cliente;


            buscador.focus();


            window._buscadorAtomo =
                buscador;


            return {
                ok: true,

                fechaDesde:
                    fechas[0].value,

                fechaHasta:
                    fechas[1].value,

                cliente:
                    buscador.value
            };
            """,

            FECHA_HOY,
            CLIENTE
        )
    )


    if not resultado_filtros.get(
        "ok"
    ):

        raise Exception(
            "No se pudieron configurar "
            "los filtros."
        )


    print(
        "Fecha desde:",
        FECHA_HOY
    )

    print(
        "Fecha hasta:",
        FECHA_HOY
    )

    print(
        "Cliente: ATOMO"
    )


    time.sleep(2)


    # =====================================================
    # 6. EJECUTAR BÚSQUEDA
    # =====================================================

    print()
    print(
        "Ejecutando búsqueda..."
    )


    resultado_buscar = (
        driver.execute_script(
            """
            var buscador =
                window._buscadorAtomo;


            if (!buscador) {
                return 'NO_BUSCADOR';
            }


            var rectBuscador =
                buscador.getBoundingClientRect();


            var elementos =
                document.getElementsByTagName(
                    '*'
                );


            var boton = null;

            var mejorDistancia =
                99999;


            for (
                var i = 0;
                i < elementos.length;
                i++
            ) {

                var elemento =
                    elementos[i];


                if (
                    elemento == buscador
                ) {
                    continue;
                }


                var rect =
                    elemento.getBoundingClientRect();


                if (
                    rect.width <= 0 ||
                    rect.height <= 0
                ) {
                    continue;
                }


                var distanciaX =
                    rect.left -
                    rectBuscador.right;


                var diferenciaY =
                    Math.abs(
                        rect.top -
                        rectBuscador.top
                    );


                if (
                    distanciaX >= 0 &&
                    distanciaX <= 60 &&
                    diferenciaY <= 15 &&
                    distanciaX < mejorDistancia
                ) {

                    boton =
                        elemento;

                    mejorDistancia =
                        distanciaX;

                }

            }


            if (boton) {

                try {

                    boton.click();

                    return 'CLICK';

                }

                catch(e) {

                    try {

                        boton.fireEvent(
                            'onclick'
                        );

                        return 'FIREEVENT';

                    }

                    catch(e2) {}

                }

            }


            return 'NO_ACCION';
            """
        )
    )


    print(
        "Método de búsqueda:",
        resultado_buscar
    )


    print(
        "Esperando resultados..."
    )


    time.sleep(7)


    # =====================================================
    # 7. BUSCAR FACTURAS RESULTANTES
    # =====================================================

    print()
    print(
        "Leyendo facturas filtradas..."
    )


    facturas = (
        driver.execute_script(
            """
            var links =
                document.getElementsByTagName(
                    'a'
                );

            var resultados = [];


            for (
                var i = 0;
                i < links.length;
                i++
            ) {

                var link =
                    links[i];


                var texto =
                    (
                        link.innerText ||
                        link.textContent ||
                        ''
                    );


                texto =
                    texto.replace(
                        /^\\s+|\\s+$/g,
                        ''
                    );


                if (
                    texto.indexOf('FV/') == 0
                ) {

                    resultados.push({

                        texto:
                            texto,

                        href:
                            link.getAttribute(
                                'href'
                            ) || '',

                        onclick:
                            link.getAttribute(
                                'onclick'
                            ) || '',

                        target:
                            link.getAttribute(
                                'target'
                            ) || '',

                        outerHTML:
                            link.outerHTML || ''

                    });

                }

            }


            return resultados;
            """
        )
    )


    print()
    print(
        "Facturas encontradas:",
        len(facturas)
    )


    if len(facturas) == 0:

        print()
        print(
            "No hay facturas de ATOMO "
            "para la fecha de hoy."
        )


    else:

        print()

        for numero, factura in enumerate(
            facturas,
            start=1
        ):

            print(
                numero,
                "-",
                factura["texto"]
            )


    # =====================================================
    # 8. GUARDAR DATOS DE LAS FACTURAS
    # =====================================================

    archivo_facturas = (
        BASE_DIR
        / "facturas_atomo_encontradas.txt"
    )


    with open(
        archivo_facturas,
        "w",
        encoding="utf-8",
        errors="ignore"
    ) as archivo:


        archivo.write(
            "FECHA: "
            + FECHA_HOY
            + "\n"
        )

        archivo.write(
            "CLIENTE: ATOMO\n"
        )

        archivo.write(
            "CANTIDAD: "
            + str(len(facturas))
            + "\n"
        )

        archivo.write(
            "\n"
        )


        for numero, factura in enumerate(
            facturas,
            start=1
        ):


            archivo.write(
                "====================================\n"
            )

            archivo.write(
                "FACTURA "
                + str(numero)
                + "\n"
            )

            archivo.write(
                "====================================\n"
            )


            archivo.write(
                "TEXTO: "
                + factura["texto"]
                + "\n"
            )


            archivo.write(
                "HREF: "
                + factura["href"]
                + "\n"
            )


            archivo.write(
                "ONCLICK: "
                + factura["onclick"]
                + "\n"
            )


            archivo.write(
                "TARGET: "
                + factura["target"]
                + "\n"
            )


            archivo.write(
                "HTML:\n"
                + factura["outerHTML"]
                + "\n"
            )


            archivo.write(
                "\n"
            )


    print()
    print(
        "Información guardada en:"
    )

    print(
        archivo_facturas
    )


    print()
    print(
        "Carpeta de futuras descargas:"
    )

    print(
        DOWNLOADS_DIR
    )


    print()
    print(
        "FILTRO TERMINADO CORRECTAMENTE."
    )


except Exception as error:

    print()
    print(
        "ERROR DURANTE LA AUTOMATIZACIÓN"
    )

    print(
        type(error).__name__
    )

    print(
        error
    )


input(
    "\nPresioná ENTER para cerrar "
    "el navegador..."
)


try:

    driver.quit()

except Exception:

    pass