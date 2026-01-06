"""Module for launching the show_md UI """
import sys
import markdown
from PyQt5.QtWidgets import (QApplication,QDialog) # pylint: disable=E0611
from PyQt5 import uic

class ShowMd(QDialog): # pylint: disable=R0903
    """ dialog window for showing markdown or text files"""
    def __init__(self, parent=None,file=None):
        """
        initialize class

        Parameters:
            parent (class): self from parent calling this class
            input_data (dict): input data for plotting
            opts (dict): plot options for data
            tooltips (dict): optional tooltips to display over hovered items
        
        Returns:
            None.
        """

        super().__init__(parent)
        uic.loadUi("ui/show_md.ui", self)

        self.file = file

        #display markdown file
        if file:
            self.setWindowTitle(file)
            with open(file,"r",encoding="utf-8") as f:
                md_text = f.read()

            if file.lower().endswith(".md"):
                html = markdown.markdown(md_text,extensions=["fenced_code"])
            else:
                html = f"<pre class='plaintext'>{md_text}</pre>"

            # Add simple CSS styling for readability
            styled_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 12px; }}
                    pre {{ background: #f4f4f4; padding: 8px; border-radius: 4px; }}
                    code {{ font-family: Consolas, monospace; }}
                    pre.plaintext {{
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        font-family: Consolas, monospace;
                        background: #fdfdfd;
                    }}
                </style>
            </head>
            <body>
                {html}
            </body>
            </html>
            """

            self.textBrowser.setHtml(styled_html)

if __name__ == "__main__":
    app = QApplication([])
    w = ShowMd(file="README.md")
    # w = ShowMd(file="LICENSE")

    w.show()
    sys.exit(app.exec_())
