from selenium import webdriver
from selenium.webdriver.ie.service import Service

from config import (
    IEDRIVER_PATH,
    LOG_PATH,
    TRILAY_URL,
)


def crear_driver():

    options = webdriver.IeOptions()

    options.attach_to_edge_chrome = True

    options.page_load_strategy = "none"

    options.initial_browser_url = TRILAY_URL


    service = Service(
        executable_path=str(IEDRIVER_PATH),
        log_output=str(LOG_PATH),
        log_level="TRACE",
    )


    driver = webdriver.Ie(
        service=service,
        options=options,
    )

    return driver