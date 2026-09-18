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
