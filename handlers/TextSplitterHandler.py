
from typing import Generator, List
from models.Message import Message
from models.Page import Page, PageSection, SplitPage
from models.PageDetail import PageDetail
from services.Logger import Logger
import re


DEFAULT_OVERLAP_PERCENT = 10  # See semantic search article for 10% overlap performance
DEFAULT_SECTION_LENGTH = 1000  # Roughly 400-500 tokens for English

ENCODING_MODEL = "text-embedding-ada-002"

STANDARD_WORD_BREAKS = [",", ";", ":", " ", "(", ")", "[", "]", "{", "}", "\t", "\n"]

# See W3C document https://www.w3.org/TR/jlreq/#cl-01
CJK_WORD_BREAKS = [
    "、",
    "，",
    "；",
    "：",
    "（",
    "）",
    "【",
    "】",
    "「",
    "」",
    "『",
    "』",
    "〔",
    "〕",
    "〈",
    "〉",
    "《",
    "》",
    "〖",
    "〗",
    "〘",
    "〙",
    "〚",
    "〛",
    "〝",
    "〞",
    "〟",
    "〰",
    "–",
    "—",
    "‘",
    "’",
    "‚",
    "‛",
    "“",
    "”",
    "„",
    "‟",
    "‹",
    "›",
]

STANDARD_SENTENCE_ENDINGS = [".", "!", "?"]

# See CL05 and CL06, based on JIS X 4051:2004
# https://www.w3.org/TR/jlreq/#cl-04
CJK_SENTENCE_ENDINGS = ["。", "！", "？", "‼", "⁇", "⁈", "⁉"]


DEFAULT_OVERLAP_PERCENT = 10  # See semantic search article for 10% overlap performance
DEFAULT_SECTION_LENGTH = 1000  # Roughly 400-500 tokens for English

class TextSplitterHandler:
    def __init__(self):
        self.logger = Logger()
        self.sentence_endings = STANDARD_SENTENCE_ENDINGS + CJK_SENTENCE_ENDINGS
        self.word_breaks = STANDARD_WORD_BREAKS + CJK_WORD_BREAKS
        self.max_section_length = DEFAULT_SECTION_LENGTH
        self.sentence_search_limit = 100
        self.section_overlap = int(self.max_section_length * DEFAULT_OVERLAP_PERCENT / 100)

    def split_pages(self, page_full_path: str, message: Message, pages: List[PageDetail]) -> List[PageSection]:
        def find_page(offset):
            num_pages = len(pages)
            for i in range(num_pages - 1):
                if offset >= pages[i].Offset and offset < pages[i + 1].Offset:
                    return pages[i].Index
            return pages[num_pages - 1].Index

        all_text = "".join(page.Text for page in pages)
        if len(all_text.strip()) == 0:
            return
        page_sections = []
        length = len(all_text)
        start = 0
        end = length
        while start + self.section_overlap < length:
            last_word = -1
            end = start + self.max_section_length

            if end > length:
                end = length
            else:
                # Try to find the end of the sentence
                while (
                    end < length
                    and (end - start - self.max_section_length) < self.sentence_search_limit
                    and all_text[end] not in self.sentence_endings
                ):
                    if all_text[end] in self.word_breaks:
                        last_word = end
                    end += 1
                if end < length and all_text[end] not in self.sentence_endings and last_word > 0:
                    end = last_word  # Fall back to at least keeping a whole word
            if end < length:
                end += 1

            # Try to find the start of the sentence or at least a whole word boundary
            last_word = -1
            while (
                start > 0
                and start > end - self.max_section_length - 2 * self.sentence_search_limit
                and all_text[start] not in self.sentence_endings
            ):
                if all_text[start] in self.word_breaks:
                    last_word = start
                start -= 1
            if all_text[start] not in self.sentence_endings and last_word > 0:
                start = last_word
            if start > 0:
                start += 1

            section_text = all_text[start:end]
            page_sections.append(PageSection(
                id = re.sub(r'[^0-9a-zA-Z_-]', '_', f'{page_full_path}-{start}').lstrip('_'),
                content=section_text,
                source_page=self.original_blob_name_with_file_page_ref(message.fileName, message.storageFilePath, page_full_path),
                source_file=page_full_path,
                original_doc_source=message.storageFilePath,
                theme=message.theme,
                sub_theme=message.subtheme
            ))

            last_table_start = section_text.rfind("<table")
            if last_table_start > 2 * self.sentence_search_limit and last_table_start > section_text.rfind("</table"):
                # If the section ends with an unclosed table, we need to start the next section with the table.
                # If table starts inside sentence_search_limit, we ignore it, as that will cause an infinite loop for tables longer than MAX_SECTION_LENGTH
                # If last table starts inside section_overlap, keep overlapping
                self.logger.info(
                    f"Section ends with unclosed table, starting next section with the table at page {find_page(start)} offset {start} table start {last_table_start}"
                )
                start = min(end - self.section_overlap, start + last_table_start)
            else:
                start = end - self.section_overlap

        if start + self.section_overlap < end:
            page_sections.append(PageSection(
                id = re.sub(r'[^0-9a-zA-Z_-]', '_', f'{page_full_path}-{start}').lstrip('_'),
                content=section_text,
                source_page=self.original_blob_name_with_file_page_ref(message.fileName, message.storageFilePath, page_full_path),
                source_file=page_full_path,
                original_doc_source=message.storageFilePath,
                theme=message.theme,
                sub_theme=message.subtheme
            ))
        return page_sections
    
    def original_blob_name_with_file_page_ref(self, file_name: str, original_file_path: str, page_name_full_path: str) -> str:
        page_no = page_name_full_path.split('-')[-1].split('.')[0]
        file_name_without_ext = file_name.split('.')[0]
        original_file_path = original_file_path.rsplit('/', 1)[0] + '/' + file_name_without_ext + '/' + file_name

        if page_no.isdigit():
            return f"{original_file_path}#page={page_no}"
        else:
            return original_file_path