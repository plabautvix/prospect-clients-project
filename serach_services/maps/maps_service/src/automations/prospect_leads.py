import os
import json
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import pika


options = Options()


def call_back_rabbitmq(ch, method, properties, body):
    print(" [x] Received %r" % body)


def send_message_rabbitmq(message_json: dict, channel):
    channel.basic_publish(exchange='fila_mensagens',
                          routing_key='enviar',
                          body=json.dumps(message_json),
                          properties=pika.BasicProperties(
                              delivery_mode=2,  # make message persistent
                          ))
    print(" [x] Sent %r" % message_json)

def insert_leads(leads, token):
    url = "http://localhost:8000/leads/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=leads, headers=headers)
    if response.status_code == 201:
        print("Leads inserted successfully.")
    else:
        print(f"Failed to insert leads. Status code: {response.status_code}, Response: {response.text}")


snap_firefox_real = "/snap/firefox/current/usr/lib/firefox/firefox"
if os.path.exists(snap_firefox_real):
    options.binary_location = snap_firefox_real

def prospect_leads(text_serach: str, message_text, stop_event, token, channel_rabbitmq) -> dict:
    """
    This function uses Selenium to scrape lead information from Google Maps
    based on the provided search text.
    Args:
        text_serach (str): The text to search for on Google Maps.
        message_text (str): The message text to be used for leads.
        stop_event (threading.Event): An event to signal when to stop the scraping process.
        token (str): The authentication token for API requests.
        channel_rabbitmq: The RabbitMQ channel for sending messages.
    Returns:
        dict: A dictionary containing a list of leads with their contact information.
    """
    print("recebeu token:", token)
    driver = webdriver.Firefox(options=options)
    driver.get("https://www.google.com/maps/search/")
    text_input_search = driver.find_element(By.ID, "searchboxinput")
    text_input_search.clear()

    time.sleep(2)
    text_input_search.send_keys(text_serach)
    text_input_search.send_keys(Keys.RETURN)
    time.sleep(5)

    results_catched = []

    while True and not stop_event.is_set():
        try:
            entities_with_contacts: list[dict] = []
            results = [
                element
                for element in driver.find_elements(By.TAG_NAME, "A")
                if element not in results_catched
            ]
            process_leads(driver, results, entities_with_contacts, results_catched)

        except Exception as e:
            print(f"Error occurred: {e}")
        insert_leads(entities_with_contacts, token)
        messages_for_send = build_message_leads_scraped(entities_with_contacts, message_text)
        send_message_rabbitmq({"messages": messages_for_send}, channel_rabbitmq)
        container = driver.find_element(
            By.CSS_SELECTOR, "div[aria-label^='Resultados para']"
        )
        driver.execute_script("arguments[0].scrollBy(0, 300)", container)
        time.sleep(5)

    driver.close()


def build_message_leads_scraped(leads: list[dict], message_default: str) -> list[dict]:
    """
    This function builds a list of lead dictionaries with the operation ID included.

    Args:
        leads (list[dict]): A list of lead dictionaries.
        operation_id (int): The ID of the operation to associate with each lead.
    
    Returns:
        list[dict]: A list of lead dictionaries with the operation ID included.
    """

    messages_for_send = []

    for lead in leads:
        message_for_lead = message_default.replace("{nome}", lead.get("nome", ""))
        messages_for_send.append({
            "lead": lead["telefone"],
            "message": message_for_lead
        })


    return messages_for_send

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


def process_leads(driver, results: list, entities_with_contacts: list, results_catched: list):
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
        if len(lead.get_attribute("class").split(" ")) == 1 and lead.get_attribute("target") != "_blank":

            main_window = driver.current_window_handle
            existing_windows = set(driver.window_handles)

            lead.click()
            time.sleep(0.8)

            current_windows = set(driver.window_handles)
            new_windows = current_windows - existing_windows

            for win in new_windows:
                try:
                    driver.switch_to.window(win)
                    driver.close()
                except Exception:
                    pass

            driver.switch_to.window(main_window)


            photo_url = None
            try:
                category_element = driver.find_element(
    By.XPATH, "//button[contains(@jsaction, '.category')]"
)
                category = category_element.text
                information_for_lead = driver.find_element(
                    By.CSS_SELECTOR,
                    f"div[aria-label='Informações de {lead.get_attribute('aria-label')}']",
                )
                photo_button = driver.find_element(
                    By.CSS_SELECTOR,
                    f"button[aria-label='Foto de {lead.get_attribute('aria-label')}']",
                )
                photo_element = photo_button.find_element(By.TAG_NAME, "img")
                photo_url = photo_element.get_attribute("src")
            except Exception as e:
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

            entities_with_contacts.append(
                {
                    "telefone": phone_number_element,
                    "nome": lead.get_attribute("aria-label"),
                    "endereco": address,
                    "site": web_site_address,
                    "foto": photo_url,
                    "categoria": category
                }
            )
            results_catched.append(lead)


if __name__ == "__main__":

    leads = prospect_leads("Barbearias no espirito santo")

