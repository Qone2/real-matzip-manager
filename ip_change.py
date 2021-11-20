from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from traceback import format_exc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import requests
import time
import platform
import json
import datetime
import random
import threading

chrome_option = Options()
chrome_option.add_argument("headless")

def ip_change():

    driver = webdriver.Chrome(executable_path="./chromedriver.exe")

    driver.get("http://192.168.0.1")
    time.sleep(1)
    with open("./graph_api_secret.json", 'r', encoding="UTF8") as f:
        account = json.load(f)["router_account"]
    driver.find_element(By.ID, "login_username").send_keys(account["id"])
    time.sleep(1)
    driver.find_element(By.NAME, "login_passwd").send_keys(account["pw"])
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, ".button").click()
    time.sleep(1)
    driver.find_element(By.XPATH, "/html/body/table/tbody/tr/td[2]/div[1]/div/div[12]").click()
    time.sleep(1)
    change_mac_addr(driver)

    try:
        while driver.find_element(By.XPATH, "/html/body/form[2]/table/tbody/tr/td[3]/div/table/tbody/tr/td/table/tbody/tr/td/table[9]/tbody/tr[4]/td/div"):
            change_mac_addr(driver)
    except:
        pass
    time.sleep(10)

def change_mac_addr(driver:WebDriver):
    mac_addr = driver.find_element(By.NAME, "wan_hwaddr_x")
    for _ in range(17):
        time.sleep(0.1)
        mac_addr.send_keys(Keys.BACKSPACE)
    for _ in range(12):
        time.sleep(0.1)
        key_ascii = int(random.uniform(48, 57 + 5.99))
        if key_ascii <= 57:
            key = chr(key_ascii)
        else:
            key = chr(key_ascii + 39)
        mac_addr.send_keys(key)
    driver.find_element(By.XPATH, "/html/body/form[2]/table/tbody/tr/td[3]/div/table/tbody/tr/td/table/tbody/tr/td/div[7]/input").click()



if __name__ == "__main__":
    ip_change()
    print("ip changed")