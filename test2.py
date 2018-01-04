from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import selenium.common.exceptions
from yattag import Doc
from yattag import indent
import codecs
import tempfile
from ebook import Ebook
from models import Chapter
from models import Page
import sys
import time
import json

print("\nStarting...\n")

def get_soup(url):
	parser = 'html.parser'
	r = requests.get(url)
	data = r.text
	soup = BeautifulSoup(data, parser)
	return soup


def get_toc_element(soup, tocLoc):
	return soup.find(attrs=tocLoc)


def soupify(browser):
	return BeautifulSoup(browser.page_source, 'html.parser')


urlRR = "http://royalroadl.com/fiction/4293/the-iron-teeth-a-goblins-tale"

urlKA = "http://gravitytales.com/novel/the-kings-avatar/"

url = urlKA

soup = get_soup(url)

for script in soup.find_all('script'):
	scriptt = str(script)
	if 'ChapterGroupList' in scriptt:
		scriptt = scriptt[scriptt.index('novelId')+8:]
		scriptt = scriptt[:scriptt.index(',')].strip()
		mchaplist = 'http://gravitytales.com/api/novels/chaptergroups/'+scriptt
		mchaplistj = requests.get(mchaplist).json()
		for mchapg in mchaplistj:
			gchaplist = 'http://gravitytales.com/api/novels/chaptergroup/'+str(mchapg['ChapterGroupId'])
			gchaplistj = requests.get(gchaplist).json()
			for chap in gchaplistj:
				chaptitle = chap['Name']
				chapUrl = url+''+chap['Slug']
				print(chapUrl)

# print("Initiating Browser...")

# browser = webdriver.PhantomJS()

# browser.set_window_size(1280, 1024)
# print("Retrieving %s ..." % url)
# browser.get(url)

# actions = ActionChains(browser)

# wait = WebDriverWait(browser, 30)

# # wait.until(EC.presence_of_element_located((By.XPATH, '//head')))

# print("Waiting...")

# try:
# 	element_present = EC.presence_of_element_located((By.XPATH, '//ul[@id="chaptergroups"'))
# 	wait.until(element_present)

# except selenium.common.exceptions.TimeoutException:
# 	print("Timeout Error")
# 	time.sleep(1)

# print("Soupifying...")
# soup = soupify(browser)

# print(soup.prettify())

# navbar = soup.find('ul', id="chaptergroups")

# for chgroup in navbar.find_all('a'):
# 	link = chgroup['href']
# 	print('\nLocating @href="%s" ... ' % link, end='')
# 	e = browser.find_element_by_xpath('//ul/li/a[@href="%s"]' % link)
# 	print("Found!")
# 	actions.move_to_element(e).click().perform()

# print("\n...")
# time.sleep(1)
# print("\nSoupifying...")
# toc = soupify(browser)

# browser.close()

# # GRAVITYTALES LINKS OBTAINED, HOTDAMN

# chapterList = toc.find('div', class_="tab-content")

# print("Printing chapter links...")
# for link in chapterList.find_all('a'):
# 	print(link)

