import requests
from bs4 import BeautifulSoup
import copy
import webnovel


PARSER = 'html.parser'


class TesterThingy:


	def __init__(self, url):
		self.toc = url
		self.toc_soup = self.getSoup(url)

	def getSoup(self, url):
		r = requests.get(url)
		data = r.text
		soup = BeautifulSoup(data, PARSER)
		return soup

	#####################
	# All sources checked from this method
	#####################
	def getWebNovel(self):

		if self.urlContains("http://www.wuxiaworld.com"):
			print("WuxiaWorld Source Detected")
			return webnovel.WuxiaWorldNovel(self.toc)

		if self.urlContains("http://royalroadl.com"):
			print("RoyalRoad Source Detected")
			return webnovel.RoyalRoadNovel(self.toc)

		if self.isWordPress():
			print("WordPress Source Detected")
			return webnovel.WordPressNovel(self.toc)

		print("Not Valid Source")
		return None

	#####################

	def isWordPress(self):
		# First check if url itself contains the base domain
		if self.urlContains("wordpress.com"):
			return True
		else:
			# If not, check if the webpage is generated by WordPress
			soup = copy.copy(self.toc_soup)
			return soup.find('meta', attrs={'name': "generator", 'content': "WordPress.com"}) is not None

	def urlContains(self, substring):
		return self.toc.find(substring) is not -1


testthingy = TesterThingy("https://yoraikun.wordpress.com/7s-chapters/")

print(testthingy.isWordPress())

