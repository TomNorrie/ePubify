import contextlib
import os
import zipfile
import tempfile
import codecs
from yattag import Doc
from yattag import indent
import constants
import models


class Ebook:
	"""docstring for Ebook"""

	def __init__(self, title, ID="Unknown", author="Unknown", publisher="Unknown"):
		self.bookTitle = title
		self.bookID = ID
		self.bookAuthor = author
		self.bookPublisher = publisher
		self.chapters = []
		self.pages = []

		self.make_title_page()

	def make_title_page(self):
		doc, tag, text, line = Doc().ttl()
		doc.asis('<?xml version="1.0" encoding="utf-8"?>')
		doc.asis('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"\n  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">')
		with tag('html', xmlns="http://www.w3.org/1999/xhtml"):
			with tag('head'):
				line('title', self.bookTitle)

			doc.stag('link', href="../Styles/style.css", type="text/css", rel="stylesheet")
			with tag('body', ('id', 'epub-title')):
				line('h1', self.bookTitle)
				line('h2', "by " + self.bookAuthor)

		titlepage = models.Page('Title', indent(doc.getvalue()))
		self.pages.append(titlepage)

	def make_ToC(self):
		doc, tag, text, line = Doc().ttl()
		doc.asis('<?xml version="1.0" encoding="utf-8"?>')
		doc.asis('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"\n  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">')
		with tag('html', xmlns="http://www.w3.org/1999/xhtml"):
			with tag('head'):
				line('title', "Contents")

			doc.stag('link', href="../Styles/style.css", type="text/css", rel="stylesheet")
			with tag('body'):
				line('h1', "Table of Contents", klass="sgc-toc-title")
				for chapter in self.chapters:
					with tag('div', klass="sgc-toc-level-1"):
						line('a', chapter.getTitle(), href=chapter.getRelativePath())

		tocpage = models.Page('ToC', indent(doc.getvalue()))
		self.pages.append(tocpage)

	def make_epub(self):
		self.make_ToC()  # first we make the table of contents based on the current contents of this Ebook instance
		with tempfile.TemporaryDirectory() as td:  # we make the epub as a standard directory using tempfiles to begin with

			# First, we include the stuff that's the same in every epub file. These never change.
			# TODO This part should probably be a seperate class function
			with codecs.open(td + '/mimetype', 'w', 'utf-8') as f:
				f.write(constants.MIMETYPE)

			os.mkdir(td + '/META-INF')
			with codecs.open(td + '/META-INF/container.xml', 'w', 'utf-8') as f:
				f.write(constants.CONTAINER)

			os.mkdir(td + '/OEPBS')
			os.mkdir(td + '/OEPBS/Styles')
			with codecs.open(td + '/OEPBS/Styles/style.css', 'w', 'utf-8') as f:
				f.write(constants.CSS)

			# Now we get to the dynamic stuff
			# TODO Should probably split this up in to seperate functions

			# The OEPBS contains all the main content of the epub
			os.mkdir(td + '/OEPBS/Text')
			for chapter in self.chapters:  # here we add all of the chapters
				with codecs.open(td + '/OEPBS/' + chapter.path, 'w', 'utf-8') as f:
					f.write(chapter.content)

			for page in self.pages:  # then we add the rest of the pages
				with codecs.open(td + '/OEPBS/Text/' + page.ID + '.xhtml', 'w', 'utf-8') as f:
					f.write(page.content)

			# contents.opf contains the metadata, the manifest, and the spine
			with codecs.open(td + '/OEPBS/content.opf', 'w', 'utf-8') as f:
				doc, tag, text, line = Doc().ttl()
				doc.asis('<?xml version="1.0" encoding="UTF-8"?>')
				with tag('package', ('unique-identifier', self.bookID), xmns="http://www.idpf.org/2007/opf", version="2.0"):

					# the metadata section should speak for itself
					with tag('metadata', ('xmlns:dc', "http://purl.org/dc/elements/1.1/"),
										 ('xmlns:opf', "http://www.idpf.org/2007/opf")):
						line('dc:title', self.bookTitle)
						line('dc:creator', self.bookAuthor)
						line('dc:language', 'en-US')
						line('dc:rights', 'Public Domain')
						line('dc:publisher', self.bookPublisher)
						line('dc:identifier', self.bookID, ('opf:scheme', "UUID"), id="bookID")

					# the manifest lists ALL files contained in the epub. Notably, this includes things like embedded images.
					with tag('manifest'):
						doc.stag('item', ('media-type', "application/x-dtbncx+xml"), id="ncx", href="toc.ncx")
						doc.stag('item', ('media-type', "text/css"), id="style", href="Styles/style.css")
						for page in self.pages:
							doc.stag('item', ('media-type', "application/xhtml+xml"), id=page.ID, href=page.path)

						for chapter in self.chapters:
							doc.stag('item', ('media-type', "application/xhtml+xml"), id=chapter.ID, href=chapter.path)

					# the spine section determines what order the pages and chapters are ordered in the final epub
					with tag('spine', toc="ncx"):
						for page in self.pages:
							doc.stag('itemref', idref=page.ID)
						for chapter in self.chapters:
							doc.stag('itemref', idref=chapter.ID)

				f.write(indent(doc.getvalue()))

			# tox.ncx is a special file basically implementing the table of contents
			# TODO this should also probably be a seperate function
			with codecs.open(td + '/OEPBS/tox.ncx', 'w', 'utf-8') as f:
				doc, tag, text = Doc().tagtext()
				doc.asis('<?xml version="1.0" encoding="UTF-8"?>')
				with tag('ncx', xmlns="http://www.daisy.org/z3986/2005/ncx/", version="2005-1"):
					with tag('head'):
						doc.stag('meta', name="dtb:uid", content=self.bookID)
						doc.stag('meta', name="dtb:depth", content="1")
						doc.stag('meta', name="dtb:totalPageCount", content="0")
						doc.stag('meta', name="dtb:maxPageNumber", content="0")

					with tag('docTitle'):
						line('text', self.bookTitle)

					with tag('navMap'):
						for chapter in self.chapters:
							with tag('navPoint', id="navPoint-" + chapter.fillID):
								with tag('navLabel'):
									line('text', "Chapter " + chapter.baseID + ":" + chapter.title)

								doc.stag('content', src=chapter.path)

			# Last, we call a seperate function that creates the actual epub from the temp directory populated in this function
			self.make_epub_from_file(td)
			# Done! The Epub has been made.

	def make_epub_from_file(self, sourceDir):
		name = self.bookTitle + '.epub'
		cwd = os.getcwd()
		path = cwd + "\\" + name
		with contextlib.suppress(FileNotFoundError):
			os.remove(path)
		with zipfile.ZipFile(path, 'x') as epub:
			for base, dirs, files in os.walk(sourceDir):
				for file in files:
					fn = os.path.join(base, file)
					epub.write(fn, fn[len(sourceDir) + 1:])

