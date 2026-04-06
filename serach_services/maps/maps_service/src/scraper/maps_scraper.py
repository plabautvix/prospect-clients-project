import time
import logging
import threading

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from config.settings import settings
from scraper.lead_parser import process_leads

logger = logging.getLogger(__name__)


def _get_firefox_options() -> Options:
    options = Options()
    if settings.FIREFOX_BINARY_PATH:
        options.binary_location = settings.FIREFOX_BINARY_PATH
    if settings.SELENIUM_HEADLESS:
        options.add_argument("--headless")
    return options


def scrape_maps(search_text: str, stop_event: threading.Event, on_leads_found: callable):
    options = _get_firefox_options()
    driver = webdriver.Firefox(options=options)

    try:
        driver.get("https://www.google.com/maps/search/")
        search_input = driver.find_element(By.ID, "searchboxinput")
        search_input.clear()
        time.sleep(2)
        search_input.send_keys(search_text)
        search_input.send_keys(Keys.RETURN)
        time.sleep(5)

        results_catched = []

        while not stop_event.is_set():
            try:
                entities: list[dict] = []
                new_results = [
                    el for el in driver.find_elements(By.TAG_NAME, "A")
                    if el not in results_catched
                ]
                process_leads(driver, new_results, entities, results_catched)

                if entities:
                    on_leads_found(entities)

            except Exception:
                logger.exception("Error during scraping iteration")

            try:
                container = driver.find_element(
                    By.CSS_SELECTOR, "div[aria-label^='Resultados para']"
                )
                driver.execute_script("arguments[0].scrollBy(0, 300)", container)
            except Exception:
                logger.warning("Could not scroll results container")

            time.sleep(5)

    finally:
        driver.quit()
        logger.info("Scraper stopped for search: %s", search_text)
