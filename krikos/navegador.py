from playwright.sync_api import sync_playwright


def crear_navegador():

    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=False
    )

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