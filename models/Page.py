class Page:
    """
    A single page from a document

    Attributes:
        page_num (int): Page number
        offset (int): If the text of the entire Document was concatenated into a single string, the index of the first character on the page. For example, if page 1 had the text "hello" and page 2 had the text "world", the offset of page 2 is 5 ("hellow")
        text (str): The text of the page
    """

    def __init__(self, page_num: int, offset: int, text: str):
        self.page_num = page_num
        self.offset = offset
        self.text = text


class SplitPage:
    """
    A section of a page that has been split into a smaller chunk.
    """

    def __init__(self, page_num: int, text: str):
        self.page_num = page_num
        self.text = text

class PageSection:
    def __init__(self, id: str, content: str, source_page: str, source_file: str, theme: str, sub_theme: str, original_doc_source: str):
        self.id = id
        self.content = content
        self.source_page = source_page
        self.source_file = source_file
        self.theme = theme
        self.sub_theme = sub_theme
        self.original_doc_source = original_doc_source