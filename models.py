

class Chapter:
	"""docstring for Chapter"""
	classID = 1

	@classmethod
	def incrementID(cls):
		cls.classID += 1

	def __init__(self, title, content):
		self.baseID = str(Chapter.classID)
		self.incrementID()
		self.title = title
		self.content = content

		self.fillID = self.baseID.zfill(3)
		self.path = "Text/Chapter" + self.fillID + ".xhtml"
		self.ID = "chapter" + self.fillID

	def getTitle(self):
		return "Chapter " + self.baseID + ": " + self.title

	def getRelativePath(self):
		return "../" + self.path


class Page:
	"""docstring for Page"""

	def __init__(self, ID, content):
		self.ID = ID
		self.content = content

		self.path = "Text/" + self.ID + ".xhtml"
