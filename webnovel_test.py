from bs4 import BeautifulSoup
from ebook import Ebook
from models import Chapter
from models import Page
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from yattag import Doc
from yattag import indent
import codecs
import re
import requests
import sys
import tempfile
import time


def get_soup(url):
	parser = 'html.parser'
	r = requests.get(url)
	data = r.text
	soup = BeautifulSoup(data, parser)
	return soup


def get_element_by_attrs(soup, tocLoc):
	return soup.find(attrs=tocLoc)


def soupify(browser):
	return BeautifulSoup(browser.page_source, 'html.parser')


class WebNovel:

	base_url_pattern = re.compile(r"^.+?[^\/:](?=[?\/]|$)")

	@classmethod
	def new_novel_by_source(cls, url, possible_sources):

		for source in possible_sources:
			if source.matches_url(url):
				return source(url)

	def __init__(self, url):
		self.toc = url
		self.base_url = WebNovel.base_url_pattern.match(url)
		self.soup = get_soup(url)
		self.novel_title = "Title Unknown"
		self.novel_author = "Author Unknown"

		self.print_init()
		self.initialize_metadata()

	def print_init(self):
		print("Input URL: %s" % self.toc)
		print("Type: %s" % type(self).__name__)

	def initialize_metadata(self):
		pass


class WordPressNovel(WebNovel):

	@staticmethod
	def matches_url(url):
		return url.find("wordpress.com") != -1


class GravityTalesNovel(WebNovel):

	@staticmethod
	def matches_url(url):
		return url.find("gravitytales.com") != -1

	@staticmethod
	def get_chapter_html(soup):
		return soup.find(class_="entry-content")

	def initialize_metadata(self):
		soup = self.soup
		self.novel_title = soup.find('h3').contents[0]
		self.novel_author = soup.find(string=re.compile("Author")).parent.parent.contents[1]

	def get_chapter_links(self):
		print("Starting Browser")
		browser = webdriver.Chrome()
		actions = ActionChains(browser)
		browser.set_window_size(1280, 1024)
		print("Retrieving %s" % self.toc)
		browser.get(self.toc)

		soup = soupify(browser)
		navbar = soup.find('ul', id="chaptergroups")
		for chgroup in navbar.find_all('a'):
			print("Opening %s" % str(chgroup.string))
			link = chgroup['href']
			e = browser.find_element_by_xpath('//ul/li/a[@href="%s"]' % link)
			actions.move_to_element(e).click().perform()

		time.sleep(1)
		page = soupify(browser)
		browser.close()

		chapter_list = page.find('div', class_="tab-content")
		links = []
		print("Computing links... ", end='')
		for link in chapter_list.find_all('a'):
			links.append(self.base_url + str(link['href']))
		print("Done")
		return links

	def get_chapters(self):
		return GravityTalesNovel.get_chapter_list(self.get_chapter_links())

	@classmethod
	def get_chapter_list(cls, links):
		chapters = []
		for url in links:
			soup = get_soup(url)
			html = cls.get_chapter_html(soup)
			chapter_title = cls.get_chapter_title(html)
			print('Retrieving contents of Chapter %s""', chapter_title)
			chapter_text = cls.get_chapter_contents(html)
			chapters.append(Chapter(chapter_title, chapter_text))
		return chapters

	@staticmethod
	def get_chapter_title(html):
		return html.find('strong').content[0]

	@staticmethod
	def get_chapter_contents(html):
		return html.find('div', id="chapterContent")




class RoyalRoadNovel(WebNovel):

	@classmethod
	def matches_url(cls, url):
		return url.find("royalroadl.com") != -1


possible_sources = {WordPressNovel, GravityTalesNovel, RoyalRoadNovel}

urlWP = "https://yoraikun.wordpress.com/7s-chapters/"
urlGT = "http://gravitytales.com/novel/the-kings-avatar/"
urlRR = "http://royalroadl.com/fiction/4293/the-iron-teeth-a-goblins-tale"

url = urlGT

test_novel = WebNovel.new_novel_by_source(url, possible_sources)

print(test_novel.get_chapter_links())

clist = test_novel.get_chapters()

print(clist[1].content)