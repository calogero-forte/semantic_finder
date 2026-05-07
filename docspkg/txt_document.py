import os
import re
import logging
from .document import Document, DocumentException

logger = logging.getLogger(__name__)

class TxtDocument(Document):
    """
    This class maintains an internal representation 
    of a TXT file and provides methods to extract text per page 
    or across a section (an interval of pages).
    A page is defined as 500 words.
    """

    def __init__(self, txt_path_i):
        """
        Initialize a TxtDocument

        txt_path_i: (str) The path (absolute or relative) 
                    of the txt file to open

        Return
        -------------------
        A TxtDocument
        """
        super().__init__(path_i=txt_path_i)

        if not os.path.exists(txt_path_i):
            raise DocumentException(f"File not found: {txt_path_i}")

        if not txt_path_i.lower().endswith('.txt'):
            raise DocumentException("The given file is not a TXT")

        with open(txt_path_i, 'r', encoding='utf-8') as f:
            self.__content = f.read()

        self.__pages = self.__split_into_pages()
        
        self.last_extracted_text = ""

    ##########################################################
    # Public methods
    ##########################################################

    @property
    def page_num(self) -> int:
        """
        Return
        -------------------
        The number of pages of this TXT file
        """
        
        num = len(self.__pages)
        if num == 0: 
            return 1 
        else: 
            return num


    ##################################################

    @page_num.setter
    def page_num(self, value_i: int) -> None:
        raise Exception("The page number cannot be modified")

    ##################################################

    def get_page_text(self, page_number_i: int) -> str:
        """
        Get the text content of a specific page.

        page_number_i: (int) The page number (0-indexed).

        Return
        -------------------
        page_text_o: (str) The text content of the requested page.
        """
        if page_number_i < 0 or page_number_i >= self.page_num:
            raise DocumentException(f"Invalid page number {page_number_i}. Valid range is 0 to {self.page_num - 1}.")
            
        logger.info(f"Extracting text from page {page_number_i}")
        page_text_o = self.__pages[page_number_i]
        self.last_extracted_text = page_text_o
        return page_text_o

    ##################################################

    def get_section_text(self, start_page_i: int, end_page_i: int) -> str:
        """
        Get the text from a section defined by an interval of pages.

        start_page_i: (int) The starting page number (0-indexed).
        end_page_i:   (int) The ending page number (0-indexed, inclusive).

        Return
        -------------------
        section_text_o: (str) The text content of the requested interval of pages.
        """
        if start_page_i < 0 or start_page_i >= self.page_num:
            raise DocumentException(f"Invalid page range [{start_page_i}, {end_page_i}]. Valid range is 0 to {self.page_num - 1}.")

        if start_page_i > end_page_i:
            raise DocumentException(f"Start page {start_page_i} cannot be greater than end page {end_page_i}.")

        logger.info(f"Extracting text from pages {start_page_i} to {end_page_i}")
        
        section_text_o = "".join(self.__pages[start_page_i:end_page_i + 1])
        self.last_extracted_text = section_text_o
        
        logger.info("Text extraction completed.")
        return section_text_o

    ##################################################

    def save_last_extracted_text(self, output_file_path_i: str) -> str:
        """
        Save the last extracted text to a txt file.

        output_file_path_i: (str) Path of the output text file.

        Return
        -------------------
        output_file_path_i: (str) The same output path in input.
        """
        if not self.last_extracted_text:
            raise DocumentException("No extracted text available. Call get_page_text or get_section_text first.")

        output_dir = os.path.dirname(output_file_path_i)
        if output_dir != "":
            os.makedirs(output_dir, exist_ok=True)

        with open(output_file_path_i, "w", encoding="utf-8") as txt_file:
            txt_file.write(self.last_extracted_text)

        logger.info(f"Last extracted text successfully saved to {output_file_path_i}")
        return output_file_path_i

    ##########################################################
    # Private methods
    ##########################################################

    def __split_into_pages(self) -> list[str]:
        """
        Split text into pages of 500 words each, preserving whitespaces/newlines.

        Return
        -------------------
        (list[str]) list of pages
        """
        tokens = re.findall(r'\S+\s*', self.__content)
        return ["".join(tokens[i:i+500]) for i in range(0, len(tokens), 500)]

####################################################################################################

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="[%(name)s :  %(levelname)s] %(message)s")
    
    try:
        txt = TxtDocument('/Users/calogeroforte/Local_database/divina_commedia.txt')
        logger.info(f"Successfully loaded '{txt.file_name}' with {txt.page_num} page(s).")
        
        # Test getting the first page
        page_0 = txt.get_page_text(0)
        logger.info(f"Page 0 snippet (first 100 chars):\n{page_0[:100]}...")
        
        # Test getting a section
        if txt.page_num > 1:
            section = txt.get_section_text(0, 1)
            logger.info(f"Section [0-1] length: {len(section)} characters.")
        else:
            logger.info("Document has only 1 page, testing section [0-0].")
            section = txt.get_section_text(0, 0)
            logger.info(f"Section [0-0] length: {len(section)} characters.")
            
        # Test error handling out of bounds
        try:
            txt.get_page_text(txt.page_num)
        except DocumentException as e:
            logger.info(f"Expected error caught: {e}")

    except Exception as e:
        logger.error(f"Test failed: {e}")
