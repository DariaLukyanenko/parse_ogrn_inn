# -*- coding: utf-8 -*-
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import requests

from dotenv import load_dotenv

from random import randint
import time
import os


load_dotenv()

DIV_BTN = '//div[@class="pb-card pb-card--clickable"]'

proxy_username = os.getenv('PROXY_USERNAME')
proxy_password = os.getenv('PROXY_PASSWORD')
proxy_port = os.getenv('PROXY_PORT')


def get_proxy_ip():
    with open('Proxies.txt', 'r') as file:
        data = file.read().split()
        random_proxy = data[randint(0, len(data) - 1)]
        proxy = (f'http://{proxy_username}:{proxy_password}@'
                 f'{random_proxy}:{proxy_port}')
        print(proxy)
        return proxy


def create_browser():
    proxy_ip = get_proxy_ip()
    print(f'using {proxy_ip}')
    proxy_options = {
        'proxy': {
            'https': proxy_ip
        }
    }
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    browser = webdriver.Chrome(seleniumwire_options=proxy_options,
                               options=chrome_options)
    browser.set_window_size(1280, 11000)

    return browser


def get_wait(browser):
    return WebDriverWait(browser, 60)


def to_click(btn, browser):
    find_button = browser.find_element(By.XPATH, btn)

    # Нажатие на кнопку
    find_button.click()


def get_info_ogrn(browser, wait, ogrn_or_inn):
    try:
        browser.get(f'https://pb.nalog.ru/search.html#t=1718002842355&'
                    f'mode=search-all&queryAll={ogrn_or_inn}&'
                    f'page=1&pageSize=10')
        wait.until(
            EC.visibility_of_all_elements_located(
                (By.XPATH, '//div[@class="pb-card pb-card--clickable"]')))
        to_click(DIV_BTN, browser)
        wait.until(
            EC.visibility_of_all_elements_located(
                (By.XPATH, '//span[@class = "pb-company-name"]')))

        common_xpaths = {
            "status": "//span[@class='pb-subject-status "
                      "pb-subject-status--active']",
            "inn": "//*[contains(text(), 'ИНН:')]/following-sibling::*[1]",
            "okved": "//*[contains(text(), 'Основной вид деятельности "
                     "(ОКВЭД):')]"
                     "/following-sibling::*[1]"
        }

        labels_and_xpaths_org = {
            **common_xpaths,
            "short_name": "//*[contains(text(), 'Сокращенное наименование:')]"
                          "/following-sibling::*[1]",
            "full_name": "//*[contains(text(), 'Полное наименование:')]"
                         "/following-sibling::*[1]",
            "kpp": "//*[contains(text(), 'КПП:')]/following-sibling::*[1]",
            "address": "//*[contains(text(), 'Адрес организации:')]"
                       "/following-sibling::*[1]",
            "ogrn": "//*[contains(text(), 'ОГРН:')]/following-sibling::*[1]",
            "registration_date": "//*[contains(text(), 'Дата регистрации:')]"
                                 "/following-sibling::*[1]"
        }

        labels_and_xpaths_ip = {
            **common_xpaths,
            "name": "//*[contains(text(), 'ФИО:')]"
                    "/following-sibling::*[1]",
            "citizenship": "//*[contains(text(), "
                           "'Сведения о гражданстве:')]"
                           "/following-sibling::*[1]",
            "ogrnip": "//*[contains(text(), 'ОГРНИП:')]"
                      "/following-sibling::*[1]",
            "registration_date": "//*[contains(text(),"
                                 "'Дата постановки на учёт:')]"
                                 "/following-sibling::*[1]"
        }

        if len(ogrn_or_inn) == 13 or len(ogrn_or_inn) == 10:
            data = {
                "status": None,
                "inn": None,
                "short_name": None,
                "full_name": None,
                "kpp": None,
                "address": None,
                "registration_date": None,
                "okved": None,
                "ogrn": None,
                "boss_name": None,
                "boss_post": None
            }

            labels_and_xpaths = labels_and_xpaths_org

        elif len(ogrn_or_inn) == 15 or len(ogrn_or_inn) == 12:
            data = {
                "status": None,
                "inn": None,
                "name": None,
                "citizenship": None,
                "registration_date": None,
                "okved": None,
                "ogrnip": None
            }

            labels_and_xpaths = labels_and_xpaths_ip

        for key, xpath in labels_and_xpaths.items():
            try:
                element = browser.find_element(By.XPATH, xpath)
                data[key] = element.text
            except:
                continue

        if len(ogrn_or_inn) == 13 or len(ogrn_or_inn) == 10:
            try:
                boss_label = browser.find_element(By.XPATH,
                                                  "//*[contains(text(), "
                                                  "'Сведения о лице, имеющем право "
                                                  "без доверенности действовать "
                                                  "от имени юридического лица')]")
                boss_name_number = boss_label.find_element(By.XPATH,
                                                           ".//following::"
                                                           "div[@class='pb-company-field-value']"
                                                           "/span[@class='font-weight-bold']")
                data["boss_name"] = boss_name_number.text
                boss_post_element = boss_label.find_element(By.XPATH,
                                                            ".//following::"
                                                            "div[@class='pb-company-field-name' "
                                                            "and contains(text(), 'Должность руководителя:')]"
                                                            "/following-sibling::"
                                                            "div[@class='pb-company-field-value']")
                data["boss_post"] = boss_post_element.text
            except:
                pass
    except:
        pass

    return data


def get_ogrn_info_new(ogrn):
    try:
        response = requests.get(
            f'https://datanewton.ru/api/v2/counterparty/{ogrn}'
        )
        json_data = response.json()

        okved_main = next(
            ({"code": okved.get("code"), "value": okved.get("value")}
             for okved in json_data.get('okveds', [])
             if okved.get("main")), None)

        managers = json_data.get('managers', [])
        boss_name = managers[0].get("fio") if managers else None
        boss_post = managers[0].get("position") if managers else None

        info = {
            'inn': json_data.get('inn'),
            'ogrn': json_data.get('ogrn'),
            'kpp': json_data.get('kpp'),
            "establishment_date": json_data.get('establishment_date'),
            "liquidationDate": json_data.get("liquidationDate"),
            'region': json_data.get('region'),
            'full_name': json_data.get('full_name'),
            'short_name': json_data.get('short_name'),
            'status': json_data.get('status', {}).get("status_rus_short"),
            'address': json_data.get('address', {}).get("value"),
            "boss_name": boss_name,
            "boss_post": boss_post,
            "okveds": okved_main
        }

        return info

    except (requests.RequestException, KeyError, IndexError) as e:
        print(f"Exception occurred while fetching data from API: {e}")
        return None


def get_ogrn_by_inn(inn):
    try:
        response = requests.get(
            f'https://datanewton.ru/api/v1/counterparty?query={inn}'
            f'&active_only=false&limit=30&offset=0'
        )
        data = response.json()

        counterparties = data["data"]["counterparties"]

        for counterparty in counterparties:
            if counterparty["inn"] == inn:
                ogrn = counterparty["ogrn"]
                return(get_ogrn_info_new(ogrn))

    except (requests.RequestException, KeyError, IndexError):
        return None


def scrape_ogrn_info(ogrn_or_inn):
    if len(ogrn_or_inn) == 13 or len(ogrn_or_inn) == 15:
        ogrn = ogrn_or_inn
        data = get_ogrn_info_new(ogrn)
    else:
        inn = ogrn_or_inn
        data = get_ogrn_by_inn(inn)

    if data:
        return data

    max_retries = 2
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            browser = create_browser()
            wait = get_wait(browser)

            data = get_info_ogrn(browser, wait, ogrn_or_inn)
            if data:
                break
        except Exception:
            data = None

        if attempt < max_retries - 1:
            time.sleep(retry_delay)


    return data

