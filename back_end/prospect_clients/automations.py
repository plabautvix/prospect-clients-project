"""
This module defines a FastAPI application that uses Selenium to scrape
contact information from Google Maps for businesses in a specified location. It
collects phone numbers, names, addresses, and website URLs for a set number of
businesses and returns them as a list of dictionaries.
"""

import time
import os
from http import HTTPStatus
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from prospect_clients.src.models.schemas.data_returned_selenium import (LeadsResponse)

app = FastAPI()

options = Options()


snap_firefox_real = "/snap/firefox/current/usr/lib/firefox/firefox"
if os.path.exists(snap_firefox_real):
    options.binary_location = snap_firefox_real


@app.get(
"/leads", 
response_model=LeadsResponse,
status_code=HTTPStatus.OK,
response_description="A list of leads with their contact information."
)
def read_route():
    """
    This function uses Selenium to scrape contact information from Google Maps
    for businesses in a specified location. It collects phone numbers, names,
    addresses, and website URLs for a set number of businesses and returns them
    as a list of dictionaries.

    Returns:
        dict[str, list[dict]]: A dictionary containing a list of leads with their contact
            information.
    """
    driver = webdriver.Firefox(options=options)
    driver.get("https://www.google.com/maps/search/")
    text_input_search = driver.find_element(By.ID, "searchboxinput")
    text_input_search.clear()

    time.sleep(2)
    text_input_search.send_keys("Empresas no Espirito Santo, Em são Pedro Vitória")
    text_input_search.send_keys(Keys.RETURN)
    time.sleep(5)

    results_catched = []
    quantity_required = 20
    entities_with_contacts: list[dict] = []

    while len(entities_with_contacts) < quantity_required:
        try:
            results = [
                element
                for element in driver.find_elements(By.TAG_NAME, "A")
                if element not in results_catched
            ]
            process_leads(driver, results, entities_with_contacts)
        except Exception as e:
            print(f"Error occurred: {e}")
        container = driver.find_element(
            By.CSS_SELECTOR, "div[aria-label^='Resultados para']"
        )
        driver.execute_script("arguments[0].scrollBy(0, 300)", container)
        time.sleep(5)
        results_catched.extend(results)

    return {"leads": entities_with_contacts}


def safe_find_element_by_css_selector(
    driver, selector: str, element_for_split: str = None
):
    """
    This function attempts to find an element using a CSS selector.

    Args:
        driver: The Selenium WebDriver instance.
        selector (str): The CSS selector to locate the element.
        element_for_split (str, optional): If provided, the function will split
            the 'aria-label' attribute of the found element using this string
            and return the second part.
    Returns:
        The found element or the processed string, or None if not found.
    """
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        if element_for_split:
            return (
                element.get_attribute("aria-label").split(element_for_split)[1].strip()
            )
        return element
    except Exception:
        return None


def process_leads(driver, results: list, entities_with_contacts: list):
    """
    This function processes a list of lead elements, extracting contact
    information for each lead and appending it to the entities_with_contacts list.

    Args:
        driver: The Selenium WebDriver instance.
        results (list): A list of lead elements to process.
        entities_with_contacts (list): A list to append the extracted contact

    Returns:
        None
    """
    for lead in results:
        if len(lead.get_attribute("class").split(" ")) == 1:
            lead.click()
            time.sleep(0.5)
            try:
                information_for_lead = driver.find_element(
                    By.CSS_SELECTOR,
                    f"div[aria-label='Informações de {lead.get_attribute('aria-label')}']",
                )
            except Exception:
                continue
            phone_number_element = safe_find_element_by_css_selector(
                information_for_lead, "button[aria-label^='Telefone:']", "Telefone:"
            )
            address: str = safe_find_element_by_css_selector(
                information_for_lead, "button[aria-label^='Endereço:']", "Endereço:"
            )
            web_site_address: str = safe_find_element_by_css_selector(
                information_for_lead, "a[aria-label^='Website:']", "Website:"
            )
            if len(entities_with_contacts) >= 20:
                return
            entities_with_contacts.append(
                {
                    "telefone": phone_number_element,
                    "nome": lead.get_attribute("aria-label"),
                    "endereco": address,
                    "site": web_site_address,
                }
            )
