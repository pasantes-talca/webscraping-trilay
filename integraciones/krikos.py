from krikos.proceso import procesar_lote_krikos


def cargar_facturas_en_krikos(fecha_carpeta):
    """Ejecuta Krikos sobre la misma fecha que proceso Trilay."""

    print("Iniciando Krikos integrado...")
    print("Iniciando registro y carga de facturas en Krikos...")
    resultado = procesar_lote_krikos(fecha_carpeta)
    print("Proceso de Krikos finalizado.")
    return resultado
