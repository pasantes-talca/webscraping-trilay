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


def detalle_factura(ruta_pdf, datos=None, motivo=None):
    datos = datos or {}
    punto = str(datos.get("punto_venta") or "").strip()
    numero = str(datos.get("numero_factura") or "").strip()
    detalle = {"archivo": Path(ruta_pdf).name}
    if numero:
        detalle["numero"] = f"{punto}-{numero}" if punto else numero
    if motivo:
        detalle["motivo"] = str(motivo)
    return detalle


# ==========================================
# PREPARAR FACTURAS
# ==========================================

def preparar_facturas(
    carpetas,
    detalle=None,
):
    if detalle is None:
        detalle = {"errores": [], "omitidas": []}

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

        datos = None
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

                detalle["omitidas"].append(detalle_factura(
                    ruta_pdf, datos,
                    "Factura de cambio: este proceso solo carga facturas generales.",
                ))
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

                detalle["errores"].append(detalle_factura(
                    ruta_pdf, datos,
                    f"Tipo de factura no reconocido: {tipo or 'sin identificar'}.",
                ))
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


            motivo = f"No se pudo preparar la factura: {error}"
            try:
                mover_pdf(ruta_pdf, carpetas["errores"])
            except Exception as error_movimiento:
                motivo += f" Además, no se pudo mover el PDF: {error_movimiento}"
            detalle["errores"].append(detalle_factura(ruta_pdf, datos, motivo))


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
            "exitosas_detalle": [],
            "pendientes_detalle": [],
            "errores_detalle": [],
        }


    playwright = None
    browser = None
    context = None
    page = None


    enviadas = 0
    sin_enviar = 0
    errores = 0
    exitosas_detalle = []
    pendientes_detalle = []
    errores_detalle = []
    procesadas = set()


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
                    exitosas_detalle.append(detalle_factura(ruta_pdf, datos))
                    procesadas.add(ruta_pdf)


                # ==========================
                # CARGADA SIN ENVIAR
                # ==========================

                elif (
                    estado
                    == "cargada_sin_enviar"
                ):

                    # La dejamos en pendientes.
                    sin_enviar += 1
                    pendientes_detalle.append(detalle_factura(
                        ruta_pdf, datos,
                        "La factura se cargó en Krikos, pero el envío automático está desactivado.",
                    ))
                    procesadas.add(ruta_pdf)

                elif estado == "envio_sin_confirmar":
                    sin_enviar += 1
                    pendientes_detalle.append(detalle_factura(
                        ruta_pdf, datos,
                        "Se pulsó Enviar factura, pero Krikos no mostró la pantalla de confirmación. Verificar en Krikos antes de reintentar para evitar duplicados.",
                    ))
                    procesadas.add(ruta_pdf)


                # ==========================
                # ESTADO DESCONOCIDO
                # ==========================

                else:
                    motivo = f"Krikos devolvió un estado no reconocido: {estado!r}."
                    mover_pdf(
                        ruta_pdf,
                        carpetas[
                            "errores"
                        ],
                    )


                    errores += 1
                    errores_detalle.append(detalle_factura(ruta_pdf, datos, motivo))
                    procesadas.add(ruta_pdf)


            except Exception as error:

                print(
                    f"Error cargando "
                    f"{ruta_pdf.name}: "
                    f"{error}"
                )

                motivo = f"No se pudo cargar o enviar en Krikos: {error}"
                try:

                    mover_pdf(
                        ruta_pdf,
                        carpetas[
                            "errores"
                        ],
                    )

                except Exception as error_movimiento:
                    motivo += f" Además, no se pudo mover el PDF: {error_movimiento}"


                errores += 1
                errores_detalle.append(detalle_factura(ruta_pdf, datos, motivo))
                procesadas.add(ruta_pdf)


    except Exception as error:
        for factura in facturas:
            ruta_pdf = factura["ruta_pdf"]
            if ruta_pdf not in procesadas:
                pendientes_detalle.append(detalle_factura(
                    ruta_pdf, factura["datos"],
                    f"No se pudo iniciar o continuar Krikos: {error}",
                ))
                sin_enviar += 1

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
        "exitosas_detalle": exitosas_detalle,
        "pendientes_detalle": pendientes_detalle,
        "errores_detalle": errores_detalle,
    }


# ==========================================
# PROCESO COMPLETO KRIKOS
# ==========================================

def procesar_lote_krikos(fecha_carpeta=None):

    fecha_proceso = (
        datetime.strptime(
            fecha_carpeta,
            "%d-%m-%Y",
        )
        if fecha_carpeta
        else datetime.now()
    )

    print(
        "Fecha de proceso recibida por Krikos: "
        f"{fecha_proceso:%d-%m-%Y}"
    )

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
            raiz_servidor,
            fecha_proceso,
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

    detalle_preparacion = {"errores": [], "omitidas": []}
    facturas = preparar_facturas(carpetas, detalle_preparacion)

    resultado = cargar_facturas_krikos(facturas, carpetas)
    resultado["errores_detalle"] = (
        resultado_importacion.get("errores_detalle", [])
        + detalle_preparacion["errores"]
        + resultado["errores_detalle"]
    )
    resultado["omitidas_detalle"] = detalle_preparacion["omitidas"]
    resultado["errores"] = len(resultado["errores_detalle"])
    resultado["sin_enviar"] = len(resultado["pendientes_detalle"])


    if not facturas:

        print(
            "No hay facturas pendientes "
            "para cargar en Krikos."
        )


        return resultado


    # ======================================
    # CARGAR EN KRIKOS
    # ======================================

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
