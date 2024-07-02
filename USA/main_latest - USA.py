import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup
import random
import time
import csv
import re

logging.basicConfig(filename='error_log.txt', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class WebScraper:
    def __init__(self, driver_path, chrome_path):
        self.driver_path = driver_path
        self.chrome_path = chrome_path
        self.driver = self.initialize_driver()

    def initialize_driver(self):
        options = Options()
        options.binary_location = self.chrome_path
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--headless")
        options.add_argument("--incognito")
        options.add_argument("--disable-accelerated-2d-canvas")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-3d-apis")
        options.add_argument("--disable-webgl")
        options.add_argument("--window-size=1280,800")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--disable-translate")

        service = Service(self.driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)  # Time limit of loading page
        return driver

    def reset_driver(self):
        self.driver.quit()
        self.driver = self.initialize_driver()

    def click_element_js(self, element):
        try:
            self.driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            logging.error(f"Error clicking element using JavaScript: {str(e)}")

    def extract_links(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            return soup.find_all('a', class_='hfpxzc')
        except Exception as e:
            logging.error(f"Error extracting links: {str(e)}")
            return []

    def extract_href(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            elements = soup.find_all(class_='CsEnBe')
            for element in elements:
                if element.name.lower() == 'a':
                    url = element['href'].strip()
                    return url
            return ""
        except Exception as e:
            logging.error(f"Error extracting href: {str(e)}")
            return ""

    def extract_phone_number_and_address(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            elements = soup.find_all(class_='rogA2c')
            address = elements[0].get_text(strip=True)
            pattern = re.compile(r'\+1\s\d{3}[-.\s]?\d{3}[-.\s]?\d{4}')
            for element in elements:
                text_element = element.get_text(strip=True)
                phone = pattern.findall(text_element)
                if phone:
                    return [address, phone[0]]
            return [address, ""]
        except Exception as e:
            logging.error(f"Error extracting phone number: {str(e)}")
            return [address, ""]

    def scroll_page(self):
        try:
            for _ in range(3):
                last_link = self.driver.find_elements(By.CLASS_NAME, 'hfpxzc')[-1]
                self.driver.execute_script("arguments[0].scrollIntoView(true);", last_link)
                self.driver.execute_script("arguments[0].dispatchEvent(new KeyboardEvent('keydown', {'key': 'PageDown'}));", last_link)
                time.sleep(random.uniform(0.5, 1.0))  # Increased delay to reduce CPU usage

            last_link = self.driver.find_elements(By.CLASS_NAME, 'hfpxzc')[-1]
            self.driver.execute_script("arguments[0].dispatchEvent(new KeyboardEvent('keydown', {'key': 'PageUp'}));", last_link)
            time.sleep(random.uniform(0.5, 1.0))  # Increased delay to reduce CPU usage
            self.driver.execute_script("arguments[0].dispatchEvent(new KeyboardEvent('keydown', {'key': 'PageDown'}));", last_link)
            time.sleep(random.uniform(2.0, 3.0))  # Increased delay to reduce CPU usage
            
        except Exception as e:
            logging.error(f"Error scrolling the page: {str(e)}")

    def escape_xpath_value(self, value):
        if '"' in value and "'" in value:
            parts = value.split("'")
            return "concat('" + "', \"'\", '".join(parts) + "')"
        elif '"' in value:
            return "'{}'".format(value)
        else:
            return "\"{}\"".format(value)

    def click_element_by_aria_label(self, aria_label_click):
        try:
            escaped_label = self.escape_xpath_value(aria_label_click)
            xpath = f"//a[@aria-label={escaped_label}]"
            element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.click_element_js(element)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'CsEnBe')))  # Espera pelo carregamento da informação
        except TimeoutException:
            logging.error(f"Timeout while waiting for element with aria-label '{aria_label_click}'")
        except NoSuchElementException:
            logging.error(f"No such element: Unable to locate element with aria-label '{aria_label_click}'")
        except Exception as e:
            logging.error(f"Error clicking element with aria-label '{aria_label_click}': {str(e)}")

class QueryProcessor:
    def __init__(self, scraper):
        self.scraper = scraper

    def read_lines_from_file(self, file):
        with open(file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]

    def log_timeout(self):
        logging.error("Timeout occurred while processing link.")

    def process_queries(self, queries_file, locations_file):
        queries = self.read_lines_from_file(queries_file)
        locations = self.read_lines_from_file(locations_file)
        base_url = 'https://www.google.com/maps/search/'

        for query in queries:
            for location in locations:
                visited_links = set()
                search_term = f"{query} {location}"
                csv_file_path = f'results_{query}_{location}.csv'
                with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter=';')
                    csv_writer.writerow(['Company','Phone', 'Address', 'Website'])

                try:
                    self.scraper.driver.get(base_url + search_term)
                    WebDriverWait(self.scraper.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'hfpxzc')))

                    previous_links_count = 0

                    while True:
                        links = self.scraper.extract_links()

                        if len(links) == previous_links_count:
                            break
                        previous_links_count = len(links)

                        for link in links:
                            aria_label_click = link.get('aria-label')
                            if '·' in aria_label_click:
                                aria_label = aria_label_click.split('·')[0].strip()
                            else:
                                aria_label = aria_label_click.strip()

                            if aria_label not in visited_links:
                                visited_links.add(aria_label)
                                try:
                                    self.scraper.click_element_by_aria_label(aria_label_click)
                                    time.sleep(3)
                                    company = aria_label
                                    phone_and_address = self.scraper.extract_phone_number_and_address()
                                    address = phone_and_address[0]
                                    website = self.scraper.extract_href()
                                    phone = phone_and_address[1]

                                    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csv_file:
                                        csv_writer = csv.writer(csv_file, delimiter=';')
                                        csv_writer.writerow([company, phone, address, website])

                                except TimeoutException:
                                    self.log_timeout()
                                except (StaleElementReferenceException, NoSuchElementException):
                                    logging.error(f"Stale element reference or no such element for '{query}' in '{location}'")

                        self.scraper.scroll_page()

                    # Reset Driver
                    self.scraper.reset_driver()
                except Exception as e:
                    logging.error(f"No results found for '{query}' in '{location}', error: {str(e)}")

def main():
    try:
        driver_path = "C:\\Navigators\\chromedriver.exe"
        chrome_path = "C:\\Navigators\\chrome-win64\\chrome.exe"
        scraper = WebScraper(driver_path, chrome_path)
        processor = QueryProcessor(scraper)

        processor.process_queries('queries.txt', 'locations.txt')
    finally:
        scraper.driver.quit()

if __name__ == '__main__':
    main()
