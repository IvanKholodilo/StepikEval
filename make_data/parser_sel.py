import json
from time import sleep

import selenium
import selenium.webdriver
import selenium.webdriver.common
import selenium.webdriver.common.by
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By


def parse():
    browser = selenium.webdriver.Firefox()
    data = []
    with open('links.json', 'r') as cat_file:
        catalog = json.load(cat_file)

    print()
    print(catalog)
    print()
    for link in catalog:
        print()
        print(' -- NEW COURSE -- ')
        print()
        browser.get(link)
        button = True
        sleep(3)
        for i in range(250):
            try:
                sleep(0.2)
                button = browser.find_elements(By.CSS_SELECTOR, "button:not(.st-button_style_none).btn-details")
                button[-1].click()
            except Exception as exp:
                print(exp)
                break
        html = browser.page_source
        bs = BeautifulSoup(html, 'html.parser')
        rews = bs.find_all('div', {'class': 'show-more__content'})
        for rew in rews:
            try:
                data.append(rew.contents[0])
            except Exception as exp:
                print(exp)
                continue

    with open('data/word_list.json', 'w') as dataset:
        json.dump(data, dataset)

    print(data)

    browser.close()


if __name__ == '__main__':
    parse()
