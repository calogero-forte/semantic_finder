import os
import re
import math
import logging
import docx
from docx.opc.constants import RELATIONSHIP_TYPE
import xml.etree.ElementTree as ET
from document import Document, DocumentException
from utils import *

logger = logging.getLogger(__name__)

class WordDocument(Document):
    """
    This class maintains an internal representation 
    of a DOCX file and provides methods to search 
    through it and extract text per pages and sections.
    """

    def __init__(self, docx_path_i):
        """
        Initialize a WordDocument

        docx_path_i: (str) The path (absolute or relative) 
                     of the docx file to open

        Return
        -------------------
        A WordDocument
        """
        super().__init__(path_i=docx_path_i)

        if not os.path.exists(docx_path_i):
            raise DocumentException(f"File not found: {docx_path_i}")

        if not docx_path_i.lower().endswith('.docx'):
            raise DocumentException("The given file is not a DOCX")

        try:
            self.doc = docx.Document(docx_path_i)
            self.__toc = []
            self.__pages = []
            self.last_toc_index = -1
            self.last_extracted_text = ""
            self.__process_paragraphs_and_pages()

        except Exception as e:
            raise DocumentException(f"Failed to load DOCX: {e}")

        

    ##########################################################
    # Public methods
    ##########################################################

    @property
    def page_num(self) -> int:
        page_count = 1
        try:
            part = self.doc.part.package.part_related_by(RELATIONSHIP_TYPE.EXTENDED_PROPERTIES)
            xml_str = part.blob.decode('utf-8')
            root = ET.fromstring(xml_str)
            ns = {'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'}
            pages_elem = root.find('ep:Pages', ns)
            if pages_elem is not None and pages_elem.text.isdigit():
                page_count = max(1, int(pages_elem.text))
                return page_count
        except Exception as e:
            logger.warning(f"Could not retrieve page count from metadata, defaulting to 1. Error: {e}")


    @page_num.setter
    def page_num(self, value_i: int) -> None:
        raise Exception("The page number cannot be modified")

    @property
    def toc(self) -> list:
        if self.__toc is None or len(self.__toc) <= 1: # Only EOF is present
            raise DocumentException("The table of contents is empty.")
        return self.__toc

    ##################################################

    def get_page_text(self, page_number_i: int) -> str:
        """
        Get the text content of a specific page.
        """
        if page_number_i < 0 or page_number_i >= self.page_num:
            raise DocumentException(f"Invalid page number {page_number_i}. Valid range is 0 to {self.page_num - 1}.")
            
        logger.info(f"Extracting text from page {page_number_i}")
        page_text_o = self.__pages[page_number_i]
        self.last_extracted_text = page_text_o
        return page_text_o

    ##################################################

    def get_section_text(self, *args, **kwargs) -> str:
        """
        Hybrid method that supports both PDFDocument and TxtDocument styles.
        - PDFDocument style: get_section_text(section_frame_i: dict, fine_trimming_i: bool = False)
        - TxtDocument style: get_section_text(start_page_i: int, end_page_i: int)
        """
        if (len(args) > 0 and isinstance(args[0], dict)) or 'section_frame_i' in kwargs:
            return self._get_section_text_by_frame(*args, **kwargs)
        elif (len(args) >= 2 and isinstance(args[0], int)) or 'start_page_i' in kwargs:
            return self._get_section_text_by_range(*args, **kwargs)
        else:
            raise DocumentException("Invalid arguments for get_section_text")

    def _get_section_text_by_range(self, start_page_i: int, end_page_i: int) -> str:
        if start_page_i < 0 or start_page_i >= self.page_num:
            raise DocumentException(f"Invalid page range [{start_page_i}, {end_page_i}]. Valid range is 0 to {self.page_num - 1}.")
        if start_page_i > end_page_i:
            raise DocumentException(f"Start page {start_page_i} cannot be greater than end page {end_page_i}.")

        logger.info(f"Extracting text from pages {start_page_i} to {end_page_i}")
        actual_end = min(end_page_i, self.page_num - 1)
        
        section_text_o = "".join(self.__pages[start_page_i:actual_end + 1])
        self.last_extracted_text = section_text_o
        return section_text_o

    def _get_section_text_by_frame(self, section_frame_i: dict, fine_trimming_i: bool = False) -> str:
        page_text_o = ""
        pages_text_list = []

        start_page = section_frame_i['start']['page']
        start_index = section_frame_i['start']['index']
        end_page = section_frame_i['end']['page']
        end_index = section_frame_i['end']['index']

        sec_title_plain = str(self.__toc[start_index][1])
        sec_title_norm = normalize_string(sec_title_plain)
        next_sec_title_norm = normalize_string(str(self.__toc[end_index][1]))

        actual_end_page = min(end_page, self.page_num - 1)
        logger.info(f"Extracting text from pages {start_page} to {actual_end_page}")

        for curr_page in range(start_page, actual_end_page + 1):
            try:
                curr_lines = self.__pages[curr_page].splitlines(True)

                if curr_page == start_page:
                    curr_lines = remove_text_lines(curr_lines, sec_title_norm)

                if curr_page == end_page and self.__toc[end_index][1] != "EOF":
                    curr_lines = remove_text_lines(curr_lines, next_sec_title_norm, True)

                if fine_trimming_i:
                    curr_lines = remove_short_lines(curr_lines)

            except DocumentException as e:
                logger.error(f"Error extracting text from page {curr_page}: {e}")
                curr_lines = []
            except ValueError as e:
                logger.error(f"Error trimming text from page {curr_page}: {e}")
            finally:
                pages_text_list.append("".join(curr_lines))

        if len(pages_text_list) > 0:
            page_text_o = "".join(pages_text_list)
            self.last_extracted_text = page_text_o
            return page_text_o 
        else:
            raise DocumentException(f"Error: Unable to retrieve text from the section '{section_frame_i}'")

    ##################################################

    def get_section_by_heading(self, heading_i: str, first_occurrance_i: bool = True) -> int:
        logger.info(f"Searching for section with heading '{heading_i}'")
        
        indexes = self.__get_section_by_heading(heading_i)

        if first_occurrance_i:
            toc_index_o = indexes[0]
        else:
            sub_toc = []
            for i in indexes:
                sub_toc.append((i, self.toc[i]))

            sub_toc_sorted = self.__sort_toc_entries_by_heading(sub_toc, heading_i)
            toc_index_o = sub_toc_sorted[0][0]
        
        self.last_toc_index = toc_index_o
        logger.info(f"Section found: '{self.__toc[toc_index_o][1]}'")
        return toc_index_o

    ##################################################

    def get_section_pages(self, section_toc_index_i: int) -> dict:
        if section_toc_index_i < 0 or section_toc_index_i >= len(self.__toc):
            raise DocumentException(f"Invalid TOC index {section_toc_index_i}")

        start_toc_entry = self.__toc[section_toc_index_i]
        section_frame_o = {
            'start': {
                'index': section_toc_index_i,
                'page': int(start_toc_entry[2]) - 1,
            },
            'end': None
        }

        start_level = int(start_toc_entry[0])
        end_index = -1

        for curr_idx in range(section_toc_index_i + 1, len(self.__toc)):
            if self.__toc[curr_idx][0] <= start_level:
                end_index = curr_idx
                break

        if end_index > -1:
            section_frame_o['end'] = {
                'index': end_index,
                'page': int(self.__toc[end_index][2]) - 1,
            }
        else:
            raise DocumentException(f"The research of section {section_toc_index_i} has failed")
            
        return section_frame_o

    ##################################################

    def get_section_text_by_heading(self, heading_title_i: str) -> tuple[str, str] | str:
        logger.info(f"Getting section text by heading: '{heading_title_i}'")
        pages_text_o = ""
        section_heading_o = ""

        try:
            sec = self.get_section_by_heading(heading_title_i, first_occurrance_i=False)
            section_heading_o = self.__toc[sec][1]
            sec_frame = self.get_section_pages(sec)
            pages_text_o = self.get_section_text(section_frame_i=sec_frame, fine_trimming_i=True)

        except (DocumentException, ValueError) as e:
            logger.error(f"Error getting section text by heading: {e}")
            return ""
        else:
            self.last_extracted_text = pages_text_o
            return (section_heading_o, pages_text_o)

    ##################################################

    def save_last_extracted_text(self, output_file_path_i: str) -> str:
        if not self.last_extracted_text:
            raise DocumentException("No extracted text available.")

        output_dir = os.path.dirname(output_file_path_i)
        if output_dir != "":
            os.makedirs(output_dir, exist_ok=True)

        with open(output_file_path_i, "w", encoding="utf-8") as f:
            f.write(self.last_extracted_text)

        logger.info(f"Last extracted text successfully saved to {output_file_path_i}")
        return output_file_path_i

    ##########################################################
    # Private methods
    ##########################################################

    def __sort_toc_entries_by_heading(self, toc_entries_i: list, searched_heading_i: str) -> list:
        searched_heading_norm = normalize_string(searched_heading_i)

        def sort_func(toc_item):
            heading_level = toc_item[1][0]
            title_norm = normalize_string(str(toc_item[1][1]))
            heading_pos = title_norm.find(searched_heading_norm)

            if heading_pos < 0:
                heading_pos = len(title_norm)

            return (heading_level, heading_pos)

        return sorted(toc_entries_i, key=sort_func)

    def __get_section_by_heading(self, heading_i: str) -> list[int]:
        heading_norm = normalize_string(heading_i)

        found_indices = []
        for idx, entry in enumerate(self.__toc[:-1]): # Exclude EOF
            if heading_norm in normalize_string(entry[1]):
                found_indices.append(idx)

        if not found_indices:
            raise DocumentException(f"No section with heading '{heading_i}' found")

        return found_indices

    def __process_paragraphs_and_pages(self) -> None:
        all_text = []
        paragraphs_data = []
        total_tokens = 0
        
        # Extract all paragraphs and track tokens to map headings to pages
        for para in self.doc.paragraphs:
            text = para.text
            if not text.strip():
                continue
                
            tokens = re.findall(r'\S+\s*', text + '\n')
            paragraphs_data.append({
                'text': text,
                'tokens': tokens,
                'style': para.style.name if para.style else '',
                'token_start': total_tokens
            })
            total_tokens += len(tokens)
            all_text.extend(tokens)
            
        # Calculate tokens per page based on the total word count and metadata pages
        tokens_per_page = math.ceil(total_tokens / self.page_num) if self.page_num > 0 else 1
        if tokens_per_page == 0:
            tokens_per_page = 1
            
        for i in range(0, len(all_text), tokens_per_page):
            self.__pages.append("".join(all_text[i:i+tokens_per_page]))
            
        if len(self.__pages) < self.page_num:
            self.__pages.extend([""] * (self.page_num - len(self.__pages)))
        elif len(self.__pages) > self.page_num:
            self.__page_num = len(self.__pages)

        if self.page_num == 0:
            self.__page_num = 1
            self.__pages = [""]

        # Build TOC from headings
        for p in paragraphs_data:
            style_name = p['style']
            if style_name and style_name.startswith('Heading'):
                level = 1
                match = re.search(r'\d+', style_name)
                if match:
                    level = int(match.group())
                    
                page_idx = p['token_start'] // tokens_per_page
                self.__toc.append([level, p['text'].strip(), page_idx + 1])
                
        # Append an EOF entry to properly close the last section
        self.__toc.append([1, "EOF", self.page_num + 1])

####################################################################################################

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="[%(name)s :  %(levelname)s] %(message)s")
    
    try:
        # We can test with a dummy docx file if it exists, or create one.        
        wd = WordDocument('/Users/calogeroforte/Local_database/Dante.docx')
        logger.info(f"Loaded '{wd.file_name}' with {wd.page_num} pages.")
        
        if len(wd.toc) > 1:
            logger.info("TOC parsed successfully!")
            for entry in wd.toc:
                logger.info(f"TOC Entry: {entry}")
            
            ch1 = wd.get_section_text_by_heading('Canto IX')
            logger.info(f"Chapter IX extracted: {len(ch1[1]) if isinstance(ch1, tuple) else len(ch1)} chars.")
            wd.save_last_extracted_text('/Users/calogeroforte/Local_database/Dante_ch1.txt')
            
        page0 = wd.get_page_text(0)
        logger.info(f"Page 0 length: {len(page0)} chars.")
        logger.info(f"Page 0: {page0}")
        
    except Exception as e:
        logger.error(f"Testing failed: {e}")
    finally:
        if os.path.exists('test_doc.docx'):
            os.remove('test_doc.docx')
