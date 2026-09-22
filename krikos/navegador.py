from pathlib import Path

from playwright.sync_api import sync_playwright

from config import EDGE_PATH


def crear_navegador():

    ejecutable_edge = Path(EDGE_PATH)

    if not ejecutable_edge.is_file():
        raise FileNotFoundError(
            "No se encontro Microsoft Edge en "
            f"{ejecutable_edge}."
        )

    playwright = sync_playwright().start()

    try:
        browser = playwright.chromium.launch(
            executable_path=str(ejecutable_edge),
            headless=False,
        )
    except Exception:
        playwright.stop()
        raise

    context = browser.new_context()

    page = context.new_page()

    return playwright, browser, context, page


def cerrar_navegador(
    playwright,
    browser,
):

    try:
        browser.close()
    except Exception:
        pass

    try:
        playwright.stop()
    except Exception:
        pass
