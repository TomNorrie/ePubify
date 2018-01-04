import re
import requests
from bs4 import BeautifulSoup
from ebook import Ebook


def get_soup(url):
	parser = 'html.parser'
	r = requests.get(url)
	data = r.text
	soup = BeautifulSoup(data, parser)
	return soup


class WebNovel:

	base_url_pattern = re.compile(r"^.+?[^\/:](?=[?\/]|$)")

	def __init(self, url):
		self.toc = url
		self.base_url = WebNovel.base_url_pattern.match(url)
		self.soup = get_soup(url)
		self.title = "Title Unknown"
		self.author = "Author Unknown"

	def make_ebook(self):
		"""Makes an ebook object by iterating through each chapter url, converting it in to a chapter object, and appending it to the ebook's chapterlist"""
		ebook = Ebook(self.title)
		for link in self.get_chapter_links():
			chapter = self.makeChapter(link)
			ebook.chapters.append(chapter)
		return ebook

	def get_chapter_links(self):
		post = self.soup.find()
		pass
