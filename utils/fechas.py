from datetime import datetime, timedelta


def fecha_actual():

    return datetime.now().strftime(
        "%d/%m/%Y"
    )


def fecha_actual_carpeta():

    return datetime.now().strftime(
        "%d-%m-%Y"
    )


def fecha_dia_anterior():

    return (
        datetime.now() - timedelta(days=1)
    ).strftime("%d/%m/%Y")


def fecha_dia_anterior_carpeta():

    return (
        datetime.now() - timedelta(days=1)
    ).strftime("%d-%m-%Y")


def formatos_dia_anterior():
    ayer = datetime.now() - timedelta(days=1)
    return (
        ayer.strftime("%d/%m/%Y"),
        ayer.strftime("%d-%m-%Y"),
    )


def formatos_fecha_facturacion(fecha_texto=None):
    """Devuelve la fecha para Trilay y para el nombre de la carpeta.

    Acepta DD-MM-AAAA o DD/MM/AAAA. Si no se indica una fecha,
    utiliza el dia actual.
    """
    if fecha_texto is None or not str(fecha_texto).strip():
        fecha = datetime.now()
    else:
        valor = str(fecha_texto).strip()
        fecha = None

        for formato in ("%d-%m-%Y", "%d/%m/%Y"):
            try:
                fecha = datetime.strptime(valor, formato)
                break
            except ValueError:
                pass

        if fecha is None:
            raise ValueError(
                "Fecha invalida. Usa DD-MM-AAAA o DD/MM/AAAA, "
                "por ejemplo 17-09-2026."
            )

    return (
        fecha.strftime("%d/%m/%Y"),
        fecha.strftime("%d-%m-%Y"),
    )
