import shutil

from datetime import datetime
from pathlib import Path

from krikos.servidor import (
    conectar_servidor,
    carpeta_del_dia,
    importar_pdf,
)

from krikos.extractor import (
    extraer_datos_pdf,
)

from krikos.validaciones import (
    validar_pdf,
    validar_datos_factura,
)

from krikos.navegador import (
    crear_navegador,
    cerrar_navegador,
)

from krikos.login import (
    iniciar_sesion_krikos,
)

from krikos.cargas import (
    procesar_factura_en_pagina,
)


# ==========================================
# CREAR CARPETAS DEL DÍA
# ==========================================

def crear_carpetas_proceso(
    carpeta_dia,
):

    carpeta_dia = Path(
        carpeta_dia
    )


    carpetas = {

        "pendientes":
            carpeta_dia
            / "facturas_pendientes",

        "procesadas":
            carpeta_dia
            / "factura_procesada",

        "errores":
            carpeta_dia
            / "facturas_error",

        "cambios":
            carpeta_dia
            / "facturas_cambios",
    }


    for carpeta in carpetas.values():

        carpeta.mkdir(
            parents=True,
            exist_ok=True,
        )


    return carpetas


# ==========================================
# NOMBRE DISPONIBLE
# ==========================================

def nombre_disponible(
    carpeta,
    nombre_archivo,
):

    carpeta = Path(
        carpeta
    )


    destino = (
        carpeta
        / nombre_archivo
    )


    if not destino.exists():

        return destino


    archivo = Path(
        nombre_archivo
    )


    fecha = datetime.now().strftime(
        "%H%M%S"
    )


    return (
        carpeta
        /
        (
            f"{archivo.stem}_"
            f"{fecha}"
            f"{archivo.suffix}"
        )
    )


# ==========================================
# MOVER PDF
# ==========================================

def mover_pdf(
    ruta_pdf,
    carpeta_destino,
):

    origen = Path(
        ruta_pdf
    )


    carpeta_destino = Path(
        carpeta_destino
    )


    carpeta_destino.mkdir(
        parents=True,
        exist_ok=True,
    )


    destino = nombre_disponible(
        carpeta_destino,
        origen.name,
    )


    shutil.move(
        str(origen),
        str(destino),
    )


    return destino


# ==========================================
# PREPARAR FACTURAS
# ==========================================

def preparar_facturas(
    carpetas,
):

    pendientes = (
        carpetas[
            "pendientes"
        ]
    )


    facturas = []


    pdfs = sorted(
        pendientes.glob(
            "*.pdf"
        )
    )


    for ruta_pdf in pdfs:

        try:

            validar_pdf(
                ruta_pdf
            )


            datos = extraer_datos_pdf(
                ruta_pdf
            )


            if not datos:

                raise RuntimeError(
                    "No se pudieron extraer "
                    "los datos del PDF."
                )


            tipo = datos.get(
                "tipo_factura"
            )


            # ==================================
            # FACTURA DE CAMBIO
            # ==================================

            if tipo == "Cambio":

                mover_pdf(
                    ruta_pdf,
                    carpetas[
                        "cambios"
                    ],
                )

                continue


            # ==================================
            # TIPO DESCONOCIDO
            # ==================================

            if tipo != "General":

                mover_pdf(
                    ruta_pdf,
                    carpetas[
                        "errores"
                    ],
                )

                continue


            # ==================================
            # VALIDAR DATOS
            # ==================================

            validar_datos_factura(
                datos
            )


            facturas.append(
                {
                    "ruta_pdf":
                        ruta_pdf,

                    "datos":
                        datos,
                }
            )


        except Exception as error:

            print(
                f"Error preparando "
                f"{ruta_pdf.name}: "
                f"{error}"
            )


            try:

                mover_pdf(
                    ruta_pdf,
                    carpetas[
                        "errores"
                    ],
                )

            except Exception:
                pass


    return facturas


# ==========================================
# PROCESAR FACTURAS EN KRIKOS
# ==========================================

def cargar_facturas_krikos(
    facturas,
    carpetas,
):

    if not facturas:

        return {
            "enviadas": 0,
            "sin_enviar": 0,
            "errores": 0,
        }


    playwright = None
    browser = None
    context = None
    page = None


    enviadas = 0
    sin_enviar = 0
    errores = 0


    try:

        (
            playwright,
            browser,
            context,
            page,
        ) = crear_navegador()


        iniciar_sesion_krikos(
            page
        )


        for indice, factura in enumerate(
            facturas,
            start=1,
        ):

            ruta_pdf = (
                factura[
                    "ruta_pdf"
                ]
            )


            datos = (
                factura[
                    "datos"
                ]
            )


            print(
                f"\nFactura "
                f"{indice}/"
                f"{len(facturas)}: "
                f"{ruta_pdf.name}"
            )


            try:

                estado = (
                    procesar_factura_en_pagina(
                        page,
                        ruta_pdf,
                        datos,
                    )
                )


                # ==========================
                # ENVIADA
                # ==========================

                if estado == "enviada":

                    mover_pdf(
                        ruta_pdf,
                        carpetas[
                            "procesadas"
                        ],
                    )


                    enviadas += 1


                # ==========================
                # CARGADA SIN ENVIAR
                # ==========================

                elif (
                    estado
                    == "cargada_sin_enviar"
                ):

                    # La dejamos en pendientes.
                    sin_enviar += 1


                # ==========================
                # ESTADO DESCONOCIDO
                # ==========================

                else:

                    mover_pdf(
                        ruta_pdf,
                        carpetas[
                            "errores"
                        ],
                    )


                    errores += 1


            except Exception as error:

                print(
                    f"Error cargando "
                    f"{ruta_pdf.name}: "
                    f"{error}"
                )


                try:

                    mover_pdf(
                        ruta_pdf,
                        carpetas[
                            "errores"
                        ],
                    )

                except Exception:
                    pass


                errores += 1


    finally:

        if (
            playwright is not None
            and
            browser is not None
        ):

            cerrar_navegador(
                playwright,
                browser,
            )


    return {
        "enviadas":
            enviadas,

        "sin_enviar":
            sin_enviar,

        "errores":
            errores,
    }


# ==========================================
# PROCESO COMPLETO KRIKOS
# ==========================================

def procesar_lote_krikos():

    # ======================================
    # CONECTAR AL SERVIDOR
    # ======================================

    raiz_servidor = (
        conectar_servidor()
    )


    # ======================================
    # CARPETA DEL DÍA
    # ======================================

    carpeta_dia = (
        carpeta_del_dia(
            raiz_servidor
        )
    )


    # ======================================
    # CARPETAS DE TRABAJO
    # ======================================

    carpetas = (
        crear_carpetas_proceso(
            carpeta_dia
        )
    )


    # ======================================
    # IMPORTAR PDF GENERADOS POR TRILAY
    # ======================================

    resultado_importacion = (
        importar_pdf(
            carpeta_servidor=
                carpeta_dia,

            carpeta_pendientes=
                carpetas[
                    "pendientes"
                ],

            carpetas_locales=[
                carpetas[
                    "pendientes"
                ],
                carpetas[
                    "procesadas"
                ],
                carpetas[
                    "errores"
                ],
                carpetas[
                    "cambios"
                ],
            ],
        )
    )


    print(
        "\nImportación Krikos:"
    )

    print(
        f"  Nuevas: "
        f"{resultado_importacion['importados']}"
    )

    print(
        f"  Ya existentes: "
        f"{resultado_importacion['omitidos']}"
    )

    print(
        f"  Errores: "
        f"{resultado_importacion['errores']}"
    )


    # ======================================
    # EXTRAER Y VALIDAR
    # ======================================

    facturas = (
        preparar_facturas(
            carpetas
        )
    )


    if not facturas:

        print(
            "No hay facturas pendientes "
            "para cargar en Krikos."
        )


        return {
            "enviadas": 0,
            "sin_enviar": 0,
            "errores": 0,
        }


    # ======================================
    # CARGAR EN KRIKOS
    # ======================================

    resultado = (
        cargar_facturas_krikos(
            facturas,
            carpetas,
        )
    )


    print(
        "\nProceso Krikos finalizado."
    )

    print(
        f"  Enviadas: "
        f"{resultado['enviadas']}"
    )

    print(
        f"  Sin enviar: "
        f"{resultado['sin_enviar']}"
    )

    print(
        f"  Errores: "
        f"{resultado['errores']}"
    )


    return resultado