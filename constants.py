MIMETYPE = "application/epub+zip"

CONTAINER = """<!-- Base Container ->
<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
"""

CSS = """/* Style Sheet for ePub Books */

/* Set margins at 2% (This gives a white border around the book) */

body {margin-left:2%;
    margin-right:2%;
    margin-top:2%;
    margin-bottom:2%;}

/* Text indent will make a paragraph indent, like putting a tab at the beginning of each new paragraph
The margin settings get rid of the white space between paragraphs, again so it looks more like a book
The text-align line justifies the margins. If you don't want them justified, change it to left, or remove that line
You don't have to specify a font, but you can */

p {text-indent: .3in;
    margin-left:0;
    margin-right:0;
    margin-top:0;
    margin-bottom:0;
    text-align: justify;
    font-family:Serif;}

/* Here we make our headings centered
We've also made the headings the same font as the body text */

 h1 { text-align: center;
    font-family:Serif; }
h2 { text-align: center;
    font-family:Serif; }
h3 { text-align: center;
    font-family:Serif; }
"""