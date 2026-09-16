from datetime import datetime


def fecha_actual():

    return datetime.now().strftime(
        "%d/%m/%Y"
    )


def fecha_actual_carpeta():

    return datetime.now().strftime(
        "%d-%m-%Y"
    )