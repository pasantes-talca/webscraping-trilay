import re

try:
    import PyPDF2
except ImportError:
    import pypdf as PyPDF2

from config import (
    IMPUESTO_BEBIDAS,
    IMPUESTO_LIMA,
    IMPUESTO_SODA,
)

from krikos.obtener_gln import (
    obtener_gln_factura,
)


def identificar_tipo_factura(
    texto,
):

    tipos = re.findall(
        r"^\s*Tipo\s*:\s*([^\s]+)",
        texto,
        re.IGNORECASE
        | re.MULTILINE,
    )


    tipos = {
        tipo.casefold()
        for tipo in tipos
    }


    if len(tipos) == 1:

        return {
            "general": "General",
            "cambio": "Cambio",
        }.get(
            tipos.pop(),
            "",
        )


    return ""


def extraer_datos_pdf(
    ruta_pdf,
):

    datos = {

        "punto_venta":
            "",

        "numero_factura":
            "",

        "fecha":
            "",

        "fecha_inicio_actividad":
            "01/07/2002",

        "caea":
            "",

        "vencimiento":
            "",

        "productos":
            [],

        "subtotal":
            0,

        "impuesto_interno":
            0,

        "iva":
            0,

        "total":
            0,

        "sucursal":
            "",

        "gln":
            "",

        "tipo_factura":
            "",
    }


    try:

        # ==========================================
        # LEER PDF
        # ==========================================

        with open(
            ruta_pdf,
            "rb",
        ) as archivo:

            lector = PyPDF2.PdfReader(
                archivo
            )


            texto = "".join(

                (
                    pagina.extract_text()
                    or ""
                )
                + "\n"

                for pagina
                in lector.pages
            )


        # ==========================================
        # TIPO DE FACTURA
        # ==========================================

        datos[
            "tipo_factura"
        ] = identificar_tipo_factura(
            texto
        )


        # El proceso original solamente carga
        # facturas General.

        if (
            datos[
                "tipo_factura"
            ]
            != "General"
        ):

            return datos


        lineas = [

            linea.strip()

            for linea
            in texto.split("\n")
        ]


        # ==========================================
        # GLN + SUCURSAL
        # ==========================================

        try:

            resultado_gln = (
                obtener_gln_factura(
                    ruta_pdf
                )
            )


            if (
                resultado_gln.get(
                    "encontrado"
                )
            ):

                datos["gln"] = (
                    resultado_gln.get(
                        "gln",
                        "",
                    )
                )


                datos["sucursal"] = (
                    resultado_gln.get(
                        "sucursal_json"
                    )
                    or
                    resultado_gln.get(
                        "sucursal_trilay"
                    )
                    or
                    ""
                )


        except Exception as error:

            print(
                f"Error al obtener GLN: "
                f"{error}"
            )


        # ==========================================
        # FUNCIONES AUXILIARES
        # ==========================================

        def valor_despues_de(
            *etiquetas,
        ):

            for etiqueta in etiquetas:

                for indice, linea in enumerate(
                    lineas
                ):

                    if linea == etiqueta:

                        siguiente = (
                            indice + 1
                        )


                        while (
                            siguiente
                            < len(lineas)
                            and
                            lineas[
                                siguiente
                            ]
                            == ""
                        ):

                            siguiente += 1


                        if (
                            siguiente
                            < len(lineas)
                        ):

                            return (
                                lineas[
                                    siguiente
                                ]
                            )


            return ""


        def a_float(
            valor,
        ):

            try:

                return float(
                    valor
                )

            except (
                TypeError,
                ValueError,
            ):

                return 0.0


        # ==========================================
        # NÚMERO DE FACTURA
        # ==========================================

        for indice, linea in enumerate(
            lineas
        ):

            if (
                re.match(
                    r"COD\.\d+",
                    linea
                )
                and
                indice + 1
                < len(lineas)
            ):

                datos[
                    "numero_factura"
                ] = (
                    lineas[
                        indice + 1
                    ]
                )

                break


        # ==========================================
        # PUNTO DE VENTA
        # ==========================================

        if (
            "P.Vta.:"
            in lineas
        ):

            indice_pv = (
                lineas.index(
                    "P.Vta.:"
                )
            )


            if (
                indice_pv + 1
                < len(lineas)
            ):

                datos[
                    "punto_venta"
                ] = (
                    lineas[
                        indice_pv + 1
                    ]
                )


            if (
                indice_pv + 2
                < len(lineas)
                and
                re.match(
                    r"\d{2}/\d{2}/\d{4}",
                    lineas[
                        indice_pv + 2
                    ],
                )
            ):

                datos[
                    "fecha_inicio_actividad"
                ] = (
                    lineas[
                        indice_pv + 2
                    ]
                )


        # ==========================================
        # FECHA
        # ==========================================

        datos[
            "fecha"
        ] = valor_despues_de(
            "Fecha:"
        )


        # ==========================================
        # CAE / CAEA
        # ==========================================

        datos[
            "caea"
        ] = valor_despues_de(
            "CAEA",
            "CAE:",
            "CAE",
        )


        if not datos[
            "caea"
        ]:

            coincidencia = re.search(
                r"CAE[A]?\s*:?\s*(\d+)",
                texto,
                re.IGNORECASE,
            )


            if coincidencia:

                datos[
                    "caea"
                ] = (
                    coincidencia.group(
                        1
                    )
                )


        datos[
            "tipo_autorizacion"
        ] = (
            "CAEA"
            if (
                "CAEA" in lineas
                and
                datos["caea"]
            )
            else
            "CAE"
        )


        # ==========================================
        # VENCIMIENTO
        # ==========================================

        datos[
            "vencimiento"
        ] = valor_despues_de(
            "Fecha Vto.",
            "Fecha Vto",
            "Fecha Vto.:",
            "Vencimiento:",
        )


        if not datos[
            "vencimiento"
        ]:

            coincidencia = re.search(
                (
                    r"Fecha\s+Vto\.?\s*:?\s*"
                    r"(\d{2}/\d{2}/\d{4})"
                ),
                texto,
                re.IGNORECASE,
            )


            if coincidencia:

                datos[
                    "vencimiento"
                ] = (
                    coincidencia.group(
                        1
                    )
                )


        # ==========================================
        # PRODUCTOS
        # ==========================================

        if (
            "Importe"
            in lineas
            and
            "Subtotal"
            in lineas
        ):

            indice_inicio = (
                lineas.index(
                    "Importe"
                )
                + 1
            )


            indice_fin = (
                lineas.index(
                    "Subtotal"
                )
            )


            bloque = lineas[
                indice_inicio:
                indice_fin
            ]


            for indice in range(
                0,
                len(bloque) - 6,
                7,
            ):

                (
                    codigo,
                    descripcion,
                    cantidad,
                    precio_unitario,
                    descuento,
                    impuesto_pdf,
                    importe,
                ) = bloque[
                    indice:
                    indice + 7
                ]


                if not re.match(
                    r"^\d+$",
                    codigo
                ):

                    continue


                cantidad = a_float(
                    cantidad
                )

                precio_unitario = (
                    a_float(
                        precio_unitario
                    )
                )

                descuento = a_float(
                    descuento
                )

                impuesto_pdf = (
                    a_float(
                        impuesto_pdf
                    )
                )

                importe = a_float(
                    importe
                )


                cantidad_pdf = (
                    cantidad
                )


                # Regla especial del proyecto
                # original.

                if cantidad == 0.06:

                    cantidad = 0.5


                descripcion_lower = (
                    descripcion.lower()
                )


                # ==================================
                # IMPUESTOS INTERNOS
                # ==================================

                if (
                    "soda"
                    in descripcion_lower
                    or
                    "sifon"
                    in descripcion_lower
                    or
                    "sifón"
                    in descripcion_lower
                ):

                    impuesto_interno = (
                        IMPUESTO_SODA
                    )


                elif (
                    "lima"
                    in descripcion_lower
                ):

                    impuesto_interno = round(
                        (
                            precio_unitario
                            * cantidad
                        )
                        * IMPUESTO_LIMA,
                        2,
                    )


                elif any(
                    sabor
                    in descripcion_lower

                    for sabor in (
                        "cola",
                        "naranja",
                        "pomelo",
                    )
                ):

                    impuesto_interno = round(
                        (
                            precio_unitario
                            * cantidad
                        )
                        * IMPUESTO_BEBIDAS,
                        2,
                    )


                else:

                    impuesto_interno = (
                        impuesto_pdf
                    )


                datos[
                    "productos"
                ].append(
                    {

                        "codigo":
                            codigo,

                        "descripcion":
                            descripcion,

                        "cantidad":
                            cantidad,

                        "cantidad_pdf":
                            cantidad_pdf,

                        "precio_unitario":
                            precio_unitario,

                        "descuento":
                            descuento,

                        "impuesto_interno":
                            impuesto_interno,

                        "importe":
                            importe,
                    }
                )


        # ==========================================
        # TOTALES
        # ==========================================

        datos[
            "subtotal"
        ] = a_float(
            valor_despues_de(
                "Subtotal"
            )
        )


        datos[
            "impuesto_interno"
        ] = a_float(
            valor_despues_de(
                "Imp. Int"
            )
        )


        datos[
            "iva"
        ] = a_float(
            valor_despues_de(
                "IVA 21%"
            )
        )


        datos[
            "total"
        ] = a_float(
            valor_despues_de(
                "Total"
            )
        )


        return datos


    except Exception as error:

        print(
            f"Error al procesar "
            f"el PDF: {error}"
        )

        return None