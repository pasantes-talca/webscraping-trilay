import time

from decimal import Decimal

from config import (
    KRIKOS_URL,
    ENVIAR_FACTURA_AUTOMATICAMENTE,
    ESPERA_POST_ENVIO_MS,
)

from krikos.facturas import (
    abrir_nueva_factura,
    subir_pdf,
)

from krikos.login import bloquear_chat

from krikos.obtener_gln import (
    obtener_gln_factura,
)


# ==========================================
# FORMATO DE NÚMEROS PARA KRIKOS
# ==========================================

def decimal_coma(
    valor,
    decimales=2,
):

    numero = float(
        valor
    )

    texto = (
        f"{numero:.{decimales}f}"
        .rstrip("0")
        .rstrip(".")
    )

    return texto.replace(
        ".",
        ","
    )


# ==========================================
# ENCABEZADO
# ==========================================

def completar_encabezado(
    page,
    datos,
):

    valor_sucursal = (
        datos.get("gln")
        or
        datos.get("sucursal")
    )


    if valor_sucursal:

        campo_sucursal = page.locator(
            'input[formcontrolname="sucursal"]'
        )


        if campo_sucursal.count() > 0:

            campo_sucursal.fill(
                str(
                    valor_sucursal
                )
            )

            time.sleep(
                0.5
            )


            try:

                opcion = page.locator(
                    "mat-option:visible"
                ).first


                opcion.wait_for(
                    state="visible",
                    timeout=4000,
                )


                opcion.click()


            except Exception as error:

                print(
                    "No se pudo seleccionar "
                    f"la sucursal: {error}"
                )


    # ======================================
    # PUNTO DE VENTA
    # ======================================

    if datos.get(
        "punto_venta"
    ):

        page.fill(
            'input[formcontrolname="ptoVta"]',
            str(
                datos[
                    "punto_venta"
                ]
            ),
        )


    # ======================================
    # NÚMERO DE FACTURA
    # ======================================

    if datos.get(
        "numero_factura"
    ):

        page.fill(
            'input[formcontrolname="nroDocumento"]',
            str(
                datos[
                    "numero_factura"
                ]
            ),
        )


    # ======================================
    # FECHA DE INICIO DE ACTIVIDAD
    # ======================================

    if datos.get(
        "fecha_inicio_actividad"
    ):

        page.fill(
            "#pickerDateStartActivity",
            str(
                datos[
                    "fecha_inicio_actividad"
                ]
            ),
        )


    # ======================================
    # SUBTOTAL
    # ======================================

    if float(
        datos.get(
            "subtotal"
        )
        or 0
    ) > 0:

        subtotal_redondo = str(
            int(
                round(
                    float(
                        datos[
                            "subtotal"
                        ]
                    )
                )
            )
        )


        page.locator(
            (
                'input['
                'formcontrolname='
                '"importeTotalSinImpuestos"'
                ']'
            )
        ).fill(
            subtotal_redondo
        )


# ==========================================
# PRODUCTOS
# ==========================================

def completar_items(
    page,
    datos,
):

    bloquear_chat(
        page
    )


    filas = page.locator(
        (
            'div[formarrayname='
            '"DIVITEMS"] > div'
        )
    )


    total_productos = len(
        datos[
            "productos"
        ]
    )


    for indice, producto in enumerate(
        datos[
            "productos"
        ]
    ):

        bloquear_chat(
            page
        )


        print(
            f"Item "
            f"{indice + 1}/"
            f"{total_productos}: "
            f"{producto['codigo']} - "
            f"{producto['descripcion']}"
        )


        fila = filas.nth(
            indice
        )


        fila.wait_for(
            state="visible",
            timeout=7000,
        )


        # ==================================
        # CÓDIGO
        # ==================================

        fila.locator(
            (
                'input['
                'formcontrolname='
                '"CodigoInterno"'
                ']'
            )
        ).fill(
            str(
                producto[
                    "codigo"
                ]
            )
        )


        # ==================================
        # DESCRIPCIÓN
        # ==================================

        fila.locator(
            (
                'input['
                'formcontrolname='
                '"DescripcionItem"'
                ']'
            )
        ).fill(
            str(
                producto[
                    "descripcion"
                ]
            )
        )


        # ==================================
        # CANTIDAD
        # ==================================

        cantidad = float(
            producto[
                "cantidad"
            ]
        )


        cantidad_texto = (
            decimal_coma(
                cantidad,
                5,
            )
        )


        fila.locator(
            (
                'input['
                'formcontrolname='
                '"Cantidad"'
                ']'
            )
        ).fill(
            cantidad_texto
        )


        # ==================================
        # UNIDAD DE MEDIDA
        # ==================================

        campo_unidad = (
            fila.locator(
                (
                    'input['
                    'formcontrolname='
                    '"UnidadMedida"'
                    ']'
                )
            )
        )


        campo_unidad.fill(
            "Pack"
        )


        time.sleep(
            0.4
        )


        opcion_unidad = page.locator(
            (
                'mat-option:has-text('
                '"Pack - Bultos"'
                '):visible, '
                'mat-option:has-text('
                '"Pack"'
                '):visible'
            )
        ).first


        opcion_unidad.wait_for(
            state="visible",
            timeout=4000,
        )


        opcion_unidad.click()


        # ==================================
        # PRECIO UNITARIO
        # ==================================

        fila.locator(
            (
                'input['
                'formcontrolname='
                '"PrecioUnit"'
                ']'
            )
        ).fill(
            decimal_coma(
                producto[
                    "precio_unitario"
                ],
                2,
            )
        )


        # ==================================
        # SUBREGISTRO
        # ==================================

        campo_subregistro = (
            fila.locator(
                (
                    'input['
                    'formcontrolname='
                    '"SubRegistro"'
                    ']'
                )
            )
        )


        try:

            valor_actual = (
                campo_subregistro
                .input_value()
                or ""
            ).strip()


            if (
                not valor_actual
                or
                valor_actual
                in (
                    "0",
                    "0,00",
                    "0.00",
                    "$ 0,00",
                    "$ 0",
                )
            ):

                campo_subregistro.fill(
                    decimal_coma(
                        producto[
                            "importe"
                        ],
                        2,
                    )
                )


        except Exception as error:

            print(
                "No se pudo completar "
                "SubRegistro del item "
                f"{indice + 1}: "
                f"{error}"
            )


        # ==================================
        # AGREGAR SIGUIENTE FILA
        # ==================================

        if (
            indice
            < total_productos - 1
        ):

            bloquear_chat(
                page
            )


            boton_agregar = page.locator(
                (
                    'div[formarrayname='
                    '"DIVITEMS"] '
                    'button:has-text('
                    '"add_circle"'
                    ')'
                )
            ).last


            boton_agregar.wait_for(
                state="visible",
                timeout=5000,
            )


            boton_agregar.click()


            time.sleep(
                0.8
            )


# ==========================================
# AGRUPAR IMPUESTOS INTERNOS
# ==========================================

def agrupar_impuestos_por_sabor(
    productos,
):

    grupos = {}


    for producto in productos:

        impuesto = Decimal(
            str(
                producto.get(
                    "impuesto_interno"
                )
                or 0
            )
        )


        if impuesto <= 0:

            continue


        descripcion = str(
            producto.get(
                "descripcion",
                "",
            )
        ).strip()


        descripcion_lower = (
            descripcion.lower()
        )


        sabor = next(
            (
                sabor
                for sabor
                in (
                    "cola",
                    "naranja",
                    "pomelo",
                    "lima",
                )
                if sabor
                in descripcion_lower
            ),
            None,
        )


        if sabor:

            etiqueta = (
                f"Impuesto "
                f"{sabor.capitalize()}"
            )

        else:

            etiqueta = descripcion


        grupo = grupos.setdefault(
            etiqueta,
            {
                "descripcion":
                    etiqueta,

                "importe":
                    Decimal("0"),

                "impuesto_interno":
                    Decimal("0"),
            },
        )


        grupo[
            "importe"
        ] += Decimal(
            str(
                producto.get(
                    "importe"
                )
                or 0
            )
        )


        grupo[
            "impuesto_interno"
        ] += impuesto


    return list(
        grupos.values()
    )


# ==========================================
# IVA + IMPUESTOS INTERNOS
# ==========================================

def completar_impuestos(
    page,
    datos,
):

    bloquear_chat(
        page
    )


    # ======================================
    # IVA 21 %
    # ======================================

    selector_iva = page.locator(
        (
            'mat-select['
            'formcontrolname='
            '"porcentaje"'
            ']'
        )
    ).first


    selector_iva.click()


    page.locator(
        (
            'mat-option:has-text('
            '"21"'
            '):visible'
        )
    ).first.click()


    # ======================================
    # IMPUESTOS INTERNOS
    # ======================================

    productos_con_internos = (
        agrupar_impuestos_por_sabor(
            datos[
                "productos"
            ]
        )
    )


    if not productos_con_internos:

        return


    checkbox = page.locator(
        (
            'mat-checkbox['
            'name="internos"'
            '] input[type="checkbox"]'
        )
    ).first


    if (
        checkbox.count() > 0
        and
        not checkbox.is_checked()
    ):

        page.locator(
            (
                'mat-checkbox['
                'name="internos"'
                ']'
            )
        ).first.click()


        time.sleep(
            0.5
        )


    contenedor = page.locator(
        (
            'div[formarrayname='
            '"DIVIMPTOTAL_C07"'
            ']'
        )
    ).first


    contenedor.wait_for(
        state="visible",
        timeout=5000,
    )


    filas = contenedor.locator(
        ":scope > div"
    )


    total = len(
        productos_con_internos
    )


    for indice, producto in enumerate(
        productos_con_internos
    ):

        bloquear_chat(
            page
        )


        descripcion = str(
            producto.get(
                "descripcion",
                "",
            )
        ).strip()


        base_imponible = float(
            producto.get(
                "importe"
            )
            or 0
        )


        importe_interno = float(
            producto.get(
                "impuesto_interno"
            )
            or 0
        )


        if base_imponible:

            porcentaje = (
                importe_interno
                /
                base_imponible
                *
                100
            )

        else:

            porcentaje = 0


        fila = filas.nth(
            indice
        )


        fila.wait_for(
            state="visible",
            timeout=5000,
        )


        fila.locator(
            (
                'input['
                'formcontrolname='
                '"descripcion"'
                ']'
            )
        ).fill(
            descripcion
        )


        fila.locator(
            (
                'input['
                'formcontrolname='
                '"porcentaje"'
                ']'
            )
        ).fill(
            decimal_coma(
                porcentaje,
                4,
            )
        )


        fila.locator(
            (
                'input['
                'formcontrolname='
                '"baseImponible"'
                ']'
            )
        ).fill(
            decimal_coma(
                base_imponible,
                2,
            )
        )


        campo_importe = (
            fila.locator(
                (
                    'input['
                    'formcontrolname='
                    '"importe"'
                    ']'
                )
            )
        )


        campo_importe.fill(
            decimal_coma(
                importe_interno,
                2,
            )
        )


        campo_importe.press(
            "Tab"
        )


        time.sleep(
            0.3
        )


        if indice < total - 1:

            boton_agregar = (
                fila.locator(
                    (
                        "button:has("
                        "mat-icon:has-text("
                        '"add_circle"'
                        ")"
                        ")"
                    )
                )
                .first
            )


            boton_agregar.wait_for(
                state="visible",
                timeout=5000,
            )


            boton_agregar.click(
                timeout=5000
            )


            time.sleep(
                0.6
            )


# ==========================================
# PIE DE FACTURA
# ==========================================

def completar_pie(
    page,
    datos,
):

    tipo_autorizacion = (
        datos.get(
            "tipo_autorizacion",
            "CAE",
        )
    )


    # ======================================
    # CAE / CAEA
    # ======================================

    try:

        radio = page.locator(
            (
                "mat-radio-button:"
                f'has-text("{tipo_autorizacion}")'
            )
        )


        if radio.count() > 0:

            radio.click()

        else:

            page.locator(
                (
                    f'input[value="'
                    f'{tipo_autorizacion}'
                    f'"]'
                )
            ).click(
                force=True
            )


    except Exception:
        pass


    # ======================================
    # NÚMERO DE AUTORIZACIÓN
    # ======================================

    if datos.get(
        "caea"
    ):

        page.fill(
            (
                'input['
                'formcontrolname='
                '"nroCodAutorizacion"'
                ']'
            ),
            str(
                datos[
                    "caea"
                ]
            ),
        )


    # ======================================
    # VENCIMIENTO
    # ======================================

    if datos.get(
        "vencimiento"
    ):

        campo_vencimiento = (
            page.locator(
                (
                    'mat-form-field:'
                    'has-text("Vto") input, '
                    'input['
                    'formcontrolname='
                    '"vtoCodAutorizacion"'
                    ']'
                )
            ).first
        )


        if (
            campo_vencimiento
            .get_attribute(
                "type"
            )
            == "date"
        ):

            partes = str(
                datos[
                    "vencimiento"
                ]
            ).split(
                "/"
            )


            if len(
                partes
            ) == 3:

                campo_vencimiento.fill(
                    (
                        f"{partes[2]}-"
                        f"{partes[1]}-"
                        f"{partes[0]}"
                    )
                )

        else:

            campo_vencimiento.fill(
                str(
                    datos[
                        "vencimiento"
                    ]
                )
            )


    # ======================================
    # TOTAL
    # ======================================

    if float(
        datos.get(
            "total"
        )
        or 0
    ) > 0:

        page.locator(
            (
                'mat-form-field:'
                'has('
                'mat-label:'
                'has-text("Importe")'
                ') '
                'input['
                'formcontrolname='
                '"importe"'
                ']'
            )
        ).last.fill(
            str(
                datos[
                    "total"
                ]
            ).replace(
                ".",
                ","
            )
        )


# ==========================================
# GLN + ENVÍO
# ==========================================

def cargar_gln_y_enviar(
    page,
    ruta_pdf,
    datos,
):

    valor_gln = str(
        datos.get(
            "gln"
        )
        or ""
    ).strip()


    # Si no vino del extractor,
    # lo volvemos a buscar.

    if not valor_gln:

        resultado = (
            obtener_gln_factura(
                ruta_pdf
            )
            or {}
        )


        valor_gln = str(
            resultado.get(
                "gln"
            )
            or ""
        ).strip()


    if not valor_gln:

        raise RuntimeError(
            "No se encontró un GLN "
            "para esta factura."
        )


    # ======================================
    # TIPO DE DOCUMENTO
    # ======================================

    campo_tipo_documento = (
        page.locator(
            (
                'mat-select['
                'formcontrolname="tipo"'
                ']:visible, '
                'mat-form-field:'
                'has('
                'mat-label:'
                'has-text("Tipo de documento")'
                ') '
                'mat-select:visible'
            )
        ).last
    )


    campo_tipo_documento.wait_for(
        state="visible",
        timeout=10000,
    )


    texto_actual = ""


    try:

        texto_actual = (
            campo_tipo_documento
            .inner_text()
            or ""
        ).lower()

    except Exception:
        pass


    if (
        "orden de compra"
        not in texto_actual
    ):

        campo_tipo_documento.click()


        opcion = page.locator(
            (
                'mat-option:has-text('
                '"Orden de Compra"'
                '):visible'
            )
        ).last


        opcion.wait_for(
            state="visible",
            timeout=5000,
        )


        opcion.click()


        page.wait_for_timeout(
            250
        )


    # ======================================
    # NÚMERO DE ORDEN DE COMPRA = GLN
    # ======================================

    campo_numero = page.locator(
        (
            'input['
            'formcontrolname="nro"'
            ']'
            '[placeholder="Número"]'
            ':visible'
        )
    ).last


    campo_numero.wait_for(
        state="visible",
        timeout=10000,
    )


    campo_numero.scroll_into_view_if_needed()


    # Primer intento.

    campo_numero.click()


    campo_numero.fill(
        valor_gln
    )


    page.wait_for_timeout(
        450
    )


    actual = (
        campo_numero
        .input_value()
        or ""
    ).strip()


    # Krikos a veces limpia el campo.

    if actual != valor_gln:

        print(
            "Krikos limpió el GLN. "
            "Reintentando..."
        )


        campo_numero.click()


        campo_numero.fill(
            ""
        )


        campo_numero.fill(
            valor_gln
        )


    actual = (
        campo_numero
        .input_value()
        or ""
    ).strip()


    if actual != valor_gln:

        raise RuntimeError(
            "El GLN no quedó escrito. "
            f"Esperado={valor_gln!r}, "
            f"actual={actual!r}"
        )


    # ======================================
    # ENVÍO
    # ======================================

    if not ENVIAR_FACTURA_AUTOMATICAMENTE:

        return (
            "cargada_sin_enviar"
        )


    boton_enviar = page.locator(
        (
            'button:has-text('
            '"ENVIAR FACTURA"'
            '):visible'
        )
    ).last


    boton_enviar.wait_for(
        state="visible",
        timeout=7000,
    )


    # Es intencional que no hagamos Tab
    # ni toquemos otro campo después del GLN.

    boton_enviar.click()


    page.wait_for_timeout(
        ESPERA_POST_ENVIO_MS
    )


    try:

        page.locator(
            "#boton-nuevo-documento"
        ).wait_for(
            state="visible",
            timeout=7000,
        )

    except Exception:
        return "envio_sin_confirmar"


    return "enviada"


# ==========================================
# PROCESAR UNA FACTURA COMPLETA
# ==========================================

def procesar_factura_en_pagina(
    page,
    ruta_pdf,
    datos,
):

    if (
        datos.get(
            "tipo_factura"
        )
        != "General"
    ):

        raise RuntimeError(
            "Solo se permite cargar "
            "facturas de tipo General."
        )


    print(
        f"\nProcesando: {ruta_pdf}"
    )


    # ======================================
    # ABRIR FACTURA
    # ======================================

    abrir_nueva_factura(
        page,
        KRIKOS_URL,
    )


    # ======================================
    # SUBIR PDF
    # ======================================

    subir_pdf(
        page,
        ruta_pdf,
    )


    # ======================================
    # ENCABEZADO
    # ======================================

    completar_encabezado(
        page,
        datos,
    )


    # ======================================
    # PRODUCTOS
    # ======================================

    completar_items(
        page,
        datos,
    )


    # ======================================
    # IMPUESTOS
    # ======================================

    completar_impuestos(
        page,
        datos,
    )


    # ======================================
    # PIE
    # ======================================

    completar_pie(
        page,
        datos,
    )


    # ======================================
    # GLN + ENVÍO
    # ======================================

    bloquear_chat(
        page
    )


    estado = cargar_gln_y_enviar(
        page,
        ruta_pdf,
        datos,
    )


    return estado
