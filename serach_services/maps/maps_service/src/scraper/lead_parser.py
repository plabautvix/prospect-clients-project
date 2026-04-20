import time
import logging

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


def safe_find_element(driver, selector: str, split_key: str | None = None):
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        if split_key:
            return element.get_attribute("aria-label").split(split_key)[1].strip()
        return element
    except Exception:
        return None


def extract_lead_info(driver, lead_element) -> dict | None:
    main_window = driver.current_window_handle
    existing_windows = set(driver.window_handles)

    lead_element.click()
    time.sleep(0.8)

    # Close any new windows opened by the click
    for win in set(driver.window_handles) - existing_windows:
        try:
            driver.switch_to.window(win)
            driver.close()
        except Exception:
            pass
    driver.switch_to.window(main_window)

    lead_name = lead_element.get_attribute("aria-label")

    try:
        category_el = driver.find_element(
            By.XPATH, "//button[contains(@jsaction, '.category')]"
        )
        category = category_el.text

        info_panel = driver.find_element(
            By.CSS_SELECTOR,
            f"div[aria-label='Informações de {lead_name}']",
        )
        photo_button = driver.find_element(
            By.CSS_SELECTOR,
            f"button[aria-label='Foto de {lead_name}']",
        )
        photo_url = photo_button.find_element(By.TAG_NAME, "img").get_attribute("src")
    except Exception:
        return None

    return {
        "telefone": safe_find_element(info_panel, "button[aria-label^='Telefone:']", "Telefone:"),
        "nome": lead_name,
        "endereco": safe_find_element(info_panel, "button[aria-label^='Endereco:']", "Endereco:"),
        "site": safe_find_element(info_panel, "a[aria-label^='Website:']", "Website:"),
        "foto": photo_url,
        "categoria": category,
    }


def process_leads(driver, results: list, entities: list, seen_hrefs: set, max_leads: int = 20):
    for lead in results:
        try:
            href = lead.get_attribute("href") or ""
            class_attr = lead.get_attribute("class") or ""
            target_attr = lead.get_attribute("target") or ""
        except StaleElementReferenceException:
            continue

        if len(class_attr.split(" ")) != 1 or target_attr == "_blank":
            continue

        info = extract_lead_info(driver, lead)
        if info is None:
            continue

        entities.append(info)
        seen_hrefs.add(href)

        if len(entities) >= max_leads:
            return


def build_lead_messages(leads: list[dict], message_template: str) -> list[dict]:
    messages = []
    for lead in leads:
        if not lead.get("telefone"):
            continue
        personalized = message_template.replace("{nome}", lead.get("nome", ""))
        messages.append({"lead": lead["telefone"], "message": personalized})
    return messages
