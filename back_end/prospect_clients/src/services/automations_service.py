import time
import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from prospect_clients.src.utils.publisher import publish_message


def _get_firefox_options() -> Options:
    options = Options()
    snap_firefox_real = "/snap/firefox/current/usr/lib/firefox/firefox"
    if os.path.exists(snap_firefox_real):
        options.binary_location = snap_firefox_real
    return options


class AutomationsService:
    def activate_maps_scraping(
        self, search_text: str, message_user: str, user_id: int,
        id_operation: int, title: str | None = None,
    ) -> dict:
        # No user token is sent: the maps-service authenticates to the backend
        # with its own service credential (X-Service-Key).
        publish_message(
            "prospect/maps",
            {
                "status": 1,
                "id_operation": id_operation,
                "search_text": search_text,
                "title": title,
                "user_id": user_id,
                "message_user": message_user,
            },
        )
        return {"message": "Scraping process started"}

    def deactivate_maps_scraping(
        self, id_operation: int, user_id: int,
    ) -> dict:
        publish_message(
            "prospect/maps",
            {
                "status": 0,
                "id_operation": id_operation,
                "user_id": user_id,
            },
        )
        return {"message": "Scraping process stopped"}

    def scrape_leads_from_maps(self, search_text: str) -> dict:
        options = _get_firefox_options()
        driver = webdriver.Firefox(options=options)
        try: return self._execute_scraping(driver, search_text)
        finally: driver.quit()

    def _execute_scraping(self, driver, search_text: str) -> dict:
        driver.get("https://www.google.com/maps/search/")
        text_input = driver.find_element(By.ID, "searchboxinput")
        text_input.clear()
        time.sleep(2)
        text_input.send_keys(search_text)
        text_input.send_keys(Keys.RETURN)
        time.sleep(5)

        results_catched = []
        quantity_required = 3
        entities_with_contacts: list[dict] = []

        while len(entities_with_contacts) < quantity_required:
            try:
                results = [
                    el for el in driver.find_elements(By.TAG_NAME, "A")
                    if el not in results_catched
                ]
                self._process_leads(driver, results, entities_with_contacts, results_catched)
            except Exception as e:
                print(f"Error occurred: {e}")
            container = driver.find_element(
                By.CSS_SELECTOR, "div[aria-label^='Resultados para']"
            )
            driver.execute_script("arguments[0].scrollBy(0, 300)", container)
            time.sleep(5)

        return {"leads": entities_with_contacts}

    @staticmethod
    def _safe_find_element(driver, selector: str, split_key: str | None = None):
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            if split_key:
                return element.get_attribute("aria-label").split(split_key)[1].strip()
            return element
        except Exception:
            return None

    def _process_leads(self, driver, results, entities_with_contacts, results_catched):
        for lead in results:
            if len(lead.get_attribute("class").split(" ")) == 1:
                lead.click()
                time.sleep(0.5)
                photo_url = None
                try:
                    info_panel = driver.find_element(
                        By.CSS_SELECTOR,
                        f"div[aria-label='Informações de {lead.get_attribute('aria-label')}']",
                    )
                    photo_button = driver.find_element(
                        By.CSS_SELECTOR,
                        f"button[aria-label='Foto de {lead.get_attribute('aria-label')}']",
                    )
                    photo_url = photo_button.find_element(By.TAG_NAME, "img").get_attribute("src")
                except Exception:
                    continue

                phone = self._safe_find_element(info_panel, "button[aria-label^='Telefone:']", "Telefone:")
                address = self._safe_find_element(info_panel, "button[aria-label^='Endereço:']", "Endereço:")
                website = self._safe_find_element(info_panel, "a[aria-label^='Website:']", "Website:")

                if len(entities_with_contacts) >= 20:
                    return

                entities_with_contacts.append({
                    "telefone": phone,
                    "nome": lead.get_attribute("aria-label"),
                    "endereco": address,
                    "site": website,
                    "foto": photo_url,
                })
                results_catched.append(lead)
