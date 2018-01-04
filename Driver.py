# Main driver for Epubify program

# Special Vars
use_console_input = False

toc_url = "thingy.com"

# Helper Functions


def get_url_from_console():
	pass


def toc_is_supported(toc):
	pass


# The Program

if use_console_input:
	toc_url = get_url_from_console()


webnovel = WebNovel(toc_url)

webnovel.process()

webnovel.make_ebook().make_epub()