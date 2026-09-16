from config import (
    FECHA_DESDE,
    FECHA_HASTA,
    CLIENTE,
    SUCURSAL,
)

from trilay.navegador import crear_driver
from trilay.login import iniciar_sesion

from trilay.ventas import (
    seleccionar_sucursal,
    abrir_ventas,
    aplicar_filtros,
    obtener_facturas,
    seleccionar_facturas,
)

from trilay.impresion import imprimir_facturas_pdf

from archivos.facturas import (
    registrar_pdfs_existentes,
    organizar_pdfs_generados,
)


def main():

    driver = None

    try:

        print("Iniciando automatización Trilay...")

        driver = crear_driver()

        iniciar_sesion(
            driver
        )

        seleccionar_sucursal(
            driver,
            SUCURSAL
        )

        abrir_ventas(
            driver
        )

        aplicar_filtros(
            driver=driver,
            fecha_desde=FECHA_DESDE,
            fecha_hasta=FECHA_HASTA,
            cliente=CLIENTE,
        )

        facturas = obtener_facturas(
            driver=driver,
            fecha_desde=FECHA_DESDE,
            fecha_hasta=FECHA_HASTA,
            cliente=CLIENTE,
        )

        if not facturas:

            print(
                "No se encontraron facturas."
            )

            return

        seleccionar_facturas(
            driver,
            facturas
        )

        pdf_anteriores = (
            registrar_pdfs_existentes()
        )

        imprimir_facturas_pdf(
            driver=driver,
            facturas=facturas,
            sucursal=SUCURSAL,
        )

        archivos_movidos = (
            organizar_pdfs_generados(
                pdf_anteriores=pdf_anteriores,
                cantidad_esperada=len(facturas),
            )
        )

        print(
            f"Proceso completado. "
            f"Facturas procesadas: {len(facturas)}. "
            f"PDF organizados: {len(archivos_movidos)}."
        )

    except Exception as error:

        print(
            f"Error durante la automatización: "
            f"{type(error).__name__}: {error}"
        )

    finally:

        if driver is not None:

            try:

                driver.quit()

            except Exception:

                pass


if __name__ == "__main__":
    main()