from bs4 import BeautifulSoup
import requests
from yattag import Doc
from yattag import indent
import codecs
import tempfile
from ebook import Ebook
from models import Chapter
from models import Page
import sys


toc_url = "https://yoraikun.wordpress.com/7s-chapters/"
parser = 'html.parser'


def parseTOC(base_url):
	soup = getSoup(base_url)

	post = soup.find(class_='entry-content')

	links = []

	limit = 30
	counter = 1

	for link in post.find_all('a'):
		if counter >= limit:
			break
		url = link.get('href')
		if urlOkay(url):
			links.append(url)
		counter += 1
	return links


def urlOkay(url):
	if url is None:
		return False
	elif url.find('http://www.wuxiaworld.com/cdindex-html/b') != 0:
		return False
	elif url.find('?share') != -1:
		return False
	else:
		return True


def getSoup(url):
	r = requests.get(url)
	data = r.text
	soup = BeautifulSoup(data, parser)
	return soup


def buildChapterContent(title, elements):

	doc, tag, text = Doc().tagtext()

	doc.asis('<?xml version="1.0" encoding="utf-8"?>')
	doc.asis('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"\n  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">')

	with tag('html', xmlns="http://www.w3.org/1999/xhtml", lang="en-US"):
		with tag('head'):
			doc.stag('link', href="../Styles/style.css", type="text/css", rel="stylesheet")

		with tag('body'):
			with tag('h2'):
				text(title)
			for e in elements:
				with tag(e.name):
					text(str(e.string))
	return indent(doc.getvalue())


def parseChapter(url, titleFilter=""):
	soup = getSoup(url)
	title = str(soup.find(class_='entry-title').string)
	post = soup.find(class_='entry-content')

	title = title.replace(titleFilter, "")

	print('Parsing Chapter at %s: "%s"' % (url, title))

	elements = []

	for e in post.find_all():
		elements.append(e)

	doc = buildChapterContent(title, elements)

	return Chapter(title, doc)

print(parseChapter("https://yoraikun.wordpress.com/2015/09/08/sevens-01/").content)

# bookTitle = "Coiling Dragon"


# print('Creating ebook "%s"' % bookTitle)
# ebook = Ebook('TPN93', bookTitle)

# for link in parseTOC("http://www.wuxiaworld.com/cdindex-html/"):
# 	ebook.chapters.append(parseChapter(link))


# ebook.makeEpub()
