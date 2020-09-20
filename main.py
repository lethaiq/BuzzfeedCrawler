from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from tinydb import TinyDB, Query
from time import sleep
from sys import argv
import sqlite3
from sqlite3 import Error
import pickle
import os
import sys

links = []
driver = webdriver.Firefox()
#driver.get("https://www.buzzfeed.com/news")
wait = WebDriverWait(driver, 10)
#driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#cards = driver.find_element(By.CSS_SELECTOR, 'div.story-card')

def retrieve_sub_page(driver, url):
    driver.get(url)
    cards = driver.find_elements_by_class_name('grid-posts__item')
    print('found new {} cards'.format(len(cards)))
    for card in cards:
        link = card.find_elements_by_class_name('lede__link')
        href = link[-1].get_attribute('href')
        save_new_record(href)

def retrieve_cards(driver, card_class):
    cards = driver.find_elements_by_class_name(card_class)
    for card in cards:
        link = card.find_elements_by_tag_name('a')
        href = link[-1].get_attribute('href')
        if href not in links:
            links.append(href)
            save_new_record(href)

    driver.execute_script('var elements = document.getElementsByClassName("story-card");while(elements.length > 0){elements[0].parentNode.removeChild(elements[0]);}')
    driver.execute_script('var elements = document.getElementsByClassName("buzzblock-package");while(elements.length > 0){elements[0].parentNode.removeChild(elements[0]);}')
    driver.execute_script('var elements = document.getElementsByClassName("ad-content-ready");while(elements.length > 0){elements[0].parentNode.removeChild(elements[0]);}')

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    driver.execute_script("window.scrollTo(0, -10);")

    try:
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.story-card")))
        print('new story-cards loaded')
    except:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print('wait timed out')
        sleep(5)

def save_new_record(href):
    try:
        conn = sqlite3.connect(argv[3])
    except Error as e:
        print(e)

    cur = conn.cursor()
    while(True):
        try:
            cur.execute("SELECT * FROM hrefs WHERE link == ?", (href, ))
            break
        except:
            sleep(10)
            continue
    rows = cur.fetchall()
    if len(rows) == 0:
        sql = '''INSERT INTO hrefs(link) VALUES(?) '''
        while(True):
            try:
                cur.execute(sql, (href,))
                break
            except:
                sleep(10)
                continue
        conn.commit()
        print('inserted {} into row {}'.format(href, cur.lastrowid))
    else:
        print('already existed')
    conn.close()

def save_new_record_bk(href):
    db = TinyDB('db.json')
    q = Query()
    lookup = db.search(q.href == href)
    if len(lookup) == 0:
        db.insert({'href': href})
        print('inserted {}'.format(href))
    else:
        print('already exist')

def retrieve_main_page():
    #for i in range(5):
    while(True):
        retrieve_cards(driver)
        sleep(3)

def retrieve_sub_page_main():
    pages = 'Animals Audio Books Business Buzz Celebrity Community Entertainment Food Geeky Health Investigations LGBT Life Music Parents Podcasts Politics Puzzles Reader Rewind Science Shopping Sports Style Tech Travel Weddings World'

    i = int(argv[1])
    while(True):
        retrieve_sub_page(driver, 'https://www.buzzfeed.com/{}?p={}&z=5UKO2Y&r=1'.format(argv[2], i))
        i += 1
        sleep(3)

def save_single_page(url, driver):
    try:
        data = {}
        driver.get(url)
        data['title'] = driver.find_elements_by_class_name('buzz-title')[0].text
        data['des'] = driver.find_elements_by_class_name('buzz-dek')[0].text
        data['article'] = driver.find_elements_by_tag_name('article')[0].text
    except:
        return None
    # data = (url, data['title'], data['des'], data['article'])
    # while(True):
    #     try:
    #         cur.execute("REPLACE into articles (link, title, des, body) values(?,?,?,?)", data)
    #         conn.commit()
    #         print('updated {} into row {}'.format(href, cur.lastrowid))
    #         break
    #     except:
    #         sleep(2)
    #         continue
    return data

def retrieve_single_link(driver):
    try:
        conn = sqlite3.connect(argv[3])
    except Error as e:
        print(e)

    cur = conn.cursor()
    while(True):
        try:
            cur.execute("SELECT * FROM hrefs")
            break
        except:
            sleep(2)
            continue

    rows = cur.fetchall()
    for row in rows:
        (url, _id, downloaded) = row
        path = 'articles/{}'.format(_id)
        downloading = 'articles/{}_downloading'.format(_id)
        if not os.path.isfile(path) and not os.path.isfile(downloading):
            with open(downloading, 'w'):
                pass
            data = save_single_page(url, driver)
            if data != None:
                file = open(path, 'wb')
                pickle.dump(data,file)
                os.remove(downloading)
                print('saved article {}'.format(url))
        else:
            print('article is being downloaded or already exist')

    print('ending...')
# retrieve_single_link('https://www.buzzfeed.com/amberjamieson/13-siblings-were-held-captive-by-their-parents?utm_term=.ttx77vJAE#.fgK112qQ4', driver)
retrieve_single_link(driver)

# print(retrieve_single_link('https://www.buzzfeed.com/amberjamieson/13-siblings-were-held-captive-by-their-parents?utm_term=.ttx77vJAE#.fgK112qQ4',driver))
