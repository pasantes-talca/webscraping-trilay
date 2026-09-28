from krikos.proceso import procesar_lote_krikos


def cargar_facturas_en_krikos(fecha_carpeta, provincia, sesion=None):
    """Ejecuta Krikos sobre la misma fecha que proceso Trilay."""

    print(f"Iniciando Krikos para {provincia}...")
    print("Iniciando registro y carga de facturas en Krikos...")
    resultado = procesar_lote_krikos(fecha_carpeta, provincia, sesion=sesion)
    print(f"Proceso de Krikos finalizado para {provincia}.")
    return resultado
