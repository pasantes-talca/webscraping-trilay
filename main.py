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

from trilay.impresion import (
    imprimir_facturas_pdf,
)

from archivos.facturas import (
    registrar_pdfs_existentes,
    organizar_pdfs_generados,
)

from krikos.proceso import (
    procesar_lote_krikos,
)

from krikos.registro import (
    registrar_ejecucion,
)


def ejecutar_trilay():

    driver = None

    try:

        driver = crear_driver()

        iniciar_sesion(
            driver
        )

        seleccionar_sucursal(
            driver,
            SUCURSAL,
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
                "No se encontraron facturas "
                "en Trilay."
            )

            return []


        seleccionar_facturas(
            driver,
            facturas,
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
                pdf_anteriores=
                    pdf_anteriores,

                cantidad_esperada=
                    len(facturas),
            )
        )


        print(
            f"Trilay finalizado. "
            f"Facturas: {len(facturas)}. "
            f"PDF organizados: "
            f"{len(archivos_movidos)}."
        )


        return archivos_movidos


    finally:

        if driver is not None:

            try:

                driver.quit()

            except Exception:
                pass


def main():

    with registrar_ejecucion():

        try:

            print(
                "\nIniciando Trilay..."
            )


            archivos_generados = (
                ejecutar_trilay()
            )


            if not archivos_generados:

                print(
                    "No hay facturas nuevas "
                    "para enviar a Krikos."
                )

                return


            print(
                "\nIniciando Krikos..."
            )


            resultado_krikos = (
                procesar_lote_krikos()
            )


            print(
                "\nProceso completo finalizado."
            )


            print(
                f"Enviadas a Krikos: "
                f"{resultado_krikos['enviadas']}"
            )


            print(
                f"Sin enviar: "
                f"{resultado_krikos['sin_enviar']}"
            )


            print(
                f"Errores: "
                f"{resultado_krikos['errores']}"
            )


        except Exception as error:

            print(
                "\nERROR GENERAL:"
            )

            print(
                f"{type(error).__name__}: "
                f"{error}"
            )


if __name__ == "__main__":
    main()