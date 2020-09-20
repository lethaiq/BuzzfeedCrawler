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
import urllib
from urllib.request import urlopen
import validators
from pymongo import MongoClient
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
mongo = MongoClient('mongodb://admin:admin@ds263847.mlab.com/sysfake', port=63847)

def filter_content(content):
    content = content.lower().replace('share on facebook','').replace('share on pinterest','').replace('share on email','').replace('share on link','').replace('share this link','')
    lines = (line.strip() for line in content.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    content = '\n'.join(chunk for chunk in chunks if chunk)
    return content

def main():
    buzz = mongo.sysfake.buzzfeeds
    buzz_urls = mongo.sysfake.buzzfeeds_links
    while(True):
        site = buzz_urls.find_one({"status":0})
        url = site['url']
        rt = save_single_page(url)
        if rt:
            (title, des, content) = rt
            _id = buzz.update_one({'url':url}, {"$set":{'title':title, 'des': des, 'content': content}}, upsert=True)
            if _id:
                buzz_urls.update_one({'url':url}, {"$set":{'status':1}}, upsert=True)
                print('saved content for {}'.format(url))
        else:
            buzz_urls.update_one({'url':url}, {"$set":{'status':2}}, upsert=True)
            print('cannot read url {}'.format(url))
        sleep(0.2)


def migrate():
    buzz = mongo.sysfake.buzzfeeds_links

    try:
        conn = sqlite3.connect('db.db')
    except Error as e:
        print(e)

    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM hrefs")
    except:
        sleep(2)

    rows = cur.fetchall()
    for row in rows:
        (url, _id, downloaded) = row
        _id = buzz.update_one({'url':url},{"$set":{"status":0}}, upsert=True)
        if _id:
            print('migrated for {}'.format(url))

def save_single_page(url):
    try:
        data = {}
        html = urlopen(url).read()
        soup = BeautifulSoup(html, "html5lib")
        for script in soup(["script", "style"]): # remove all javascript and stylesheet code
            script.extract()
        to_removes = soup.findAll('div', {"class":"action-bar"})
        for to_remove in to_removes:
            to_remove.decompose()

        title = filter_content(soup.findAll("h1", {"class": "buzz-title"})[0].getText())
        des = filter_content(soup.findAll("p", {"class": "buzz-dek"})[0].getText())
        content = filter_content(soup.findAll("article", {"class": "buzz"})[0].getText())
    except Exception as e:
        print(e)
        return None
    return title, des, content

main()
# migrate()
# a = save_single_page('https://www.buzzfeed.com/emmaloop/republican-memo-released?utm_term=.lxL55wAzl#.lvB33Ypyo')
# print(a)
