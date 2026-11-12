"""Acceso a Trilay con una sola sesión de Edge sin ventana."""

from datetime import datetime

from playwright.sync_api import Error as PlaywrightError, sync_playwright

from config import EDGE_PATH, SUCURSALES, TRILAY_URL
from trilay.login import PASSWORD, USUARIO


class SesionTrilay:
    def __init__(self, headless=True, slow_mo=0):
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright = None
        self.browser = None
        self.page = None
        self.listado = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        try:
            self._abrir_trilay()
            if "escritorio.asp" not in self.page.url.lower():
                self.page.locator("#txtUsuario").fill(USUARIO)
                self.page.locator("#txtPass").fill(PASSWORD)
                self.page.get_by_role("button", name="Ingresar").click()
                self.page.wait_for_url("**/escritorio.asp", timeout=60000)
            self.page.locator("#numCodJerarquia").wait_for(timeout=30000)
            return self
        except Exception:
            self.__exit__(None, None, None)
            raise

    def _abrir_trilay(self):
        """Open Trilay, falling back from Edge to bundled Chromium and retrying.

        Edge may block the site (ERR_BLOCKED_BY_CLIENT) or the server may be
        slow to answer (timeout); both used to abort the whole run.
        """
        intentos = [("Edge", EDGE_PATH), ("Chromium", None), ("Chromium", None)]
        ultimo_error = None
        for numero, (nombre, ejecutable) in enumerate(intentos, start=1):
            if self.browser is not None:
                self.browser.close()
                self.browser = None
            opciones = {"headless": self.headless, "slow_mo": self.slow_mo}
            if ejecutable:
                opciones["executable_path"] = ejecutable
            try:
                self.browser = self.playwright.chromium.launch(**opciones)
                self.page = self.browser.new_page()
                self.page.goto(TRILAY_URL, wait_until="domcontentloaded", timeout=60000)
                if numero > 1:
                    print(f"Trilay abierto con {nombre} (intento {numero}).")
                return
            except PlaywrightError as error:
                ultimo_error = error
                print(
                    f"No se pudo abrir Trilay con {nombre} (intento {numero}/{len(intentos)}): "
                    f"{str(error).splitlines()[0]}"
                )
        raise ultimo_error

    def __exit__(self, *_):
        if self.browser is not None:
            self.browser.close()
            self.browser = None
        if self.playwright is not None:
            self.playwright.stop()
            self.playwright = None

    def buscar_facturas(self, provincia, fecha, cliente, fecha_hasta=None):
        fecha_hasta = fecha_hasta or fecha
        fecha_inicio = datetime.strptime(fecha, "%d/%m/%Y").date()
        fecha_fin = datetime.strptime(fecha_hasta, "%d/%m/%Y").date()
        if fecha_fin < fecha_inicio:
            raise ValueError("La fecha final no puede ser anterior a la inicial")
        codigo = SUCURSALES[provincia]
        self.page.goto(
            TRILAY_URL.rstrip("/") + "/escritorio.asp",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        self.page.locator("#numCodJerarquia").wait_for(timeout=30000)
        seleccionado = self.page.evaluate("""codigo => {
            const selector = document.getElementById('numCodJerarquia');
            selector.value = codigo;
            cargarDivs();
            return selector.value;
        }""", codigo)
        if seleccionado != codigo:
            raise RuntimeError(f"Trilay no seleccionó {provincia}: {seleccionado}")

        self.page.wait_for_timeout(5000)
        self.page.locator("#trilay-escritorio").get_by_text(
            "Ventas", exact=True
        ).evaluate("elemento => elemento.click()")
        ventas = self.page.frame_locator("iframe[src*='ventas/ventas.asp']")
        ventas.locator("#txtFechaIni").wait_for(timeout=30000)
        frame_ventas = next(
            frame for frame in self.page.frames
            if "ventas/ventas.asp" in frame.url.lower()
        )
        valores = frame_ventas.evaluate("""({fecha, fecha_hasta, cliente}) => {
            for (const [id, valor] of [['txtFechaIni', fecha], ['txtFechaFin', fecha_hasta]]) {
                const campo = document.getElementById(id);
                campo.value = valor;
                campo.dispatchEvent(new Event('change', {bubbles: true}));
            }
            const buscador = document.getElementById('txtBusqueda');
            buscador.value = cliente;
            buscador.dispatchEvent(new Event('input', {bubbles: true}));
            document.getElementById('txtNumRegPorPag').value = '500';
            refreshlistadocoti();
            return [document.getElementById('txtFechaIni').value,
                    document.getElementById('txtFechaFin').value,
                    buscador.value];
        }""", {"fecha": fecha, "fecha_hasta": fecha_hasta, "cliente": cliente})
        if valores != [fecha, fecha_hasta, cliente]:
            raise RuntimeError(f"Los filtros de Trilay no quedaron correctos: {valores}")

        # Trilay actualiza el listado en un iframe con código heredado.
        self.page.wait_for_timeout(8000)
        self.listado = self.page.frame(name="pages")
        if self.listado is None:
            raise RuntimeError("Trilay no abrió el listado de facturas")
        facturas = self.listado.evaluate("""() => Array.from(
            document.getElementsByName('chkborrar'), check => {
                let fila = check;
                while (fila && fila.tagName !== 'TR') fila = fila.parentNode;
                return {
                    codigo: check.value,
                    fecha: check.getAttribute('artfechacomprobante') || '',
                    texto: fila ? (fila.innerText || fila.textContent || '') : ''
                };
            }
        )""")

        for factura in facturas:
            try:
                fecha_factura = datetime.strptime(
                    factura["fecha"], "%d/%m/%Y"
                ).date()
            except ValueError as error:
                raise RuntimeError(
                    f"Trilay devolvió una factura sin fecha válida: {factura['codigo']}"
                ) from error
            if not fecha_inicio <= fecha_factura <= fecha_fin or cliente.upper() not in factura["texto"].upper():
                raise RuntimeError(
                    f"El filtro de Trilay devolvió otra fecha o cliente: {factura['codigo']}"
                )
        return facturas

    def imprimir_factura(self, factura, provincia):
        """Genera un único PDF mediante la impresora PDF de Trilay."""
        if self.listado is None:
            raise RuntimeError("No hay un listado de facturas abierto")
        codigo_sucursal = SUCURSALES[provincia]
        codigo_factura = str(factura["codigo"])
        resultado = self.listado.evaluate("""({sucursal, factura}) => {
            const contenedor = document.getElementById('ImpresionMultiple');
            if (!contenedor) return false;
            contenedor.style.display = 'block';
            const anterior = document.getElementById('motor');
            if (anterior) anterior.remove();
            const motor = document.createElement('iframe');
            motor.id = 'motor';
            motor.name = 'motor';
            contenedor.appendChild(motor);
            motor.src = 'ImprimirMultiplesFacturas.asp?accion=INICIO'
                + '&CodJerarquia=' + encodeURIComponent(sucursal)
                + '&codi=' + encodeURIComponent(factura);
            return true;
        }""", {"sucursal": codigo_sucursal, "factura": codigo_factura})
        if not resultado:
            raise RuntimeError("Trilay no abrió el módulo de impresión")

        impresora = self.listado.frame_locator("#motor").locator("#cboImpresoras")
        impresora.wait_for(timeout=30000)
        valor = impresora.evaluate("""selector => {
            selector.value = 'PDF';
            selector.dispatchEvent(new Event('change', {bubbles: true}));
            return selector.value;
        }""")
        if valor != "PDF":
            raise RuntimeError("Trilay no seleccionó la impresora PDF")
        motor = self.page.frame(name="motor")
        motor.locator("#btComenzar").evaluate("boton => boton.click()")
        motor.wait_for_function("""() => Number(
            document.getElementById('porcentajeprocesado')?.textContent || 0
        ) >= 1""", timeout=120000)
