import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def visit_buff163(item_id):
    url = f"https://buff.163.com/market/item?item_id={item_id}"
    driver.get(url)

    dropdowns = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.select-box"))
    )

    results = []
    for dropdown in dropdowns:
        dropdown.click()
        time.sleep(1)

        options = dropdown.find_elements_by_css_selector("div.select-option")
        for option in options:
            option.click()
            time.sleep(1)

            selected_option = option.get_attribute("innerText").strip()
            current_url = driver.current_url

            result = {
                "dropdown": dropdown.get_attribute("innerText").strip(),
                "selected_option": selected_option,
                "url": current_url
            }
            results.append(result)

            # Return to the original URL to reset the page state
            driver.get(url)
            time.sleep(1)

    return results

def get_item_ids_and_names(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT buff_id, raw_name FROM items;"
    cursor.execute(query)

    item_ids_and_names = cursor.fetchall()
    conn.close()

    return item_ids_and_names

if __name__ == "__main__":
    db_path = "data/csgo_items.db"
    chrome_driver_path = "path/to/chromedriver"

    proxy_host = "your_proxy_host"
    proxy_port = "your_proxy_port"

    options = webdriver.ChromeOptions()
    options.add_argument(f"--proxy-server=http://{proxy_host}:{proxy_port}")
    options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path=chrome_driver_path, options=options)


    try:
        item_ids_and_names = get_item_ids_and_names(db_path)
        for item_id, raw_name in item_ids_and_names:
            print(f"Processing item {item_id} - {raw_name}")
            data = visit_buff163(item_id)
            for entry in data:
                print(entry)
    finally:
        driver.quit()
