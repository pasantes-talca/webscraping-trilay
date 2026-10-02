import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from krikos import cargas


GLN = "7798088442562"


class CargaGlnTest(unittest.TestCase):
    def test_reescribe_con_teclado_si_krikos_limpia_el_primer_intento(self):
        page = Mock()
        campo = Mock()
        campo.input_value.side_effect = ["", GLN, GLN]

        cargas.escribir_gln_estable(page, campo, GLN)

        campo.fill.assert_any_call(GLN)
        campo.press_sequentially.assert_called_once_with(GLN, delay=50)
        self.assertEqual(campo.input_value.call_count, 3)

    def test_no_acepta_un_valor_que_krikos_borra_despues(self):
        page = Mock()
        campo = Mock()
        campo.input_value.side_effect = [GLN, "", "", ""]

        with self.assertRaisesRegex(RuntimeError, "El GLN no quedó escrito"):
            cargas.escribir_gln_estable(page, campo, GLN)

        self.assertEqual(campo.press_sequentially.call_count, 2)

    def test_verifica_de_nuevo_al_aparecer_el_boton_enviar(self):
        page = Mock()
        campo_numero = Mock()
        campo_numero.input_value.return_value = ""
        boton_enviar = Mock()

        def localizar(selector):
            resultado = Mock()
            if 'formcontrolname="tipo"' in selector:
                resultado.last.inner_text.return_value = "Orden de Compra"
            elif 'formcontrolname="nro"' in selector:
                resultado.last = campo_numero
            elif "ENVIAR FACTURA" in selector:
                resultado.last = boton_enviar
            return resultado

        page.locator.side_effect = localizar
        datos = {"gln": GLN}

        with (patch.object(cargas, "escribir_gln_estable") as escribir,
              patch.object(cargas, "ENVIAR_FACTURA_AUTOMATICAMENTE", True)):
            cargas.cargar_gln_y_enviar(page, Path("factura.pdf"), datos)

        self.assertEqual(escribir.call_count, 2)
        boton_enviar.click.assert_called_once()
