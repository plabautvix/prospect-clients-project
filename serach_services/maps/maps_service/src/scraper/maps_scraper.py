import time
import logging
import threading

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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


def scrape_maps(
    search_text: str, stop_event: threading.Event, on_leads_found: callable,
    limit: int | None = None,
):
    options = _get_firefox_options()
    driver = webdriver.Firefox(options=options)

    try:
        driver.get("https://www.google.com/maps/search/")
        search_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, "#searchboxinput, #ucc-1, input[name='q']"
            ))
        )
        search_input.clear()
        time.sleep(1)
        search_input.send_keys(search_text)
        search_input.send_keys(Keys.RETURN)
        time.sleep(5)

        seen_hrefs: set[str] = set()
        collected = 0
        empty_rounds = 0
        max_empty_rounds = 5

        while not stop_event.is_set():
            try:
                entities: list[dict] = []
                all_links = driver.find_elements(By.TAG_NAME, "A")
                new_results = []
                for el in all_links:
                    try:
                        href = el.get_attribute("href") or ""
                        if href and href not in seen_hrefs:
                            new_results.append(el)
                    except Exception:
                        continue
                process_leads(driver, new_results, entities, seen_hrefs)

                if entities:
                    # Trim the batch so the run never overshoots what was asked.
                    if limit:
                        entities = entities[: limit - collected]
                    on_leads_found(entities)
                    collected += len(entities)
                    empty_rounds = 0
                    if limit and collected >= limit:
                        logger.info("Reached the requested limit of %d leads", limit)
                        break
                else:
                    empty_rounds += 1
                    logger.info("No new leads found (round %d/%d)", empty_rounds, max_empty_rounds)
                    if empty_rounds >= max_empty_rounds:
                        logger.info("No more leads after %d rounds, finishing", max_empty_rounds)
                        break

            except Exception:
                logger.exception("Error during scraping iteration")
                if entities:
                    on_leads_found(entities)

            try:
                container = driver.find_element(
                    By.CSS_SELECTOR, "div[aria-label^='Resultados para']"
                )
                driver.execute_script("arguments[0].scrollBy(0, 300)", container)
            except Exception:
                logger.warning("Could not scroll results container")

            time.sleep(5)

    except Exception:
        logger.exception("Scraper crashed for search: %s", search_text)
    finally:
        driver.quit()
        logger.info("Scraper stopped for search: %s", search_text)
