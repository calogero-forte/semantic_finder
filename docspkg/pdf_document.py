from .document import Document, DocumentException
from .utils import *
import pymupdf 
import os 
import re
import logging

logger = logging.getLogger(__name__)

class PDFDocument(Document):
    """
    This class mantains an internal representation 
    of a PDF file and, provides methods to search 
    thoughout its T.O.C. and to extract text from the pages 
    of selected chapters/sections.
    """

    def __init__(self, pdf_path_i):
        """
        Initialize a PDFHandler

        pdf_path_i: (str) The path (absolute or relative) 
                    of the pdf file to opern

        Return
        -------------------
        A PDFHandler
        """

        # Initializing parent class and 
        # relative properties
        super().__init__( path_i = pdf_path_i )

        # self.pdf_path = pdf_path_i
        # self.pdf_filename = self.__extract_pdf_filename(pdf_path_i)
    
        self.pdf = pymupdf.open(pdf_path_i)

        if(not self.pdf.is_pdf):
            raise DocumentException("The given file is not a PDF")
        else:
            #Number of pages
            # self. page_num = len (self.pdf)
            # Table of contents in format [level, title, page]
            self.toc = self.pdf.get_toc(simple = True)
            #Store the TOC index of the last found section
            self.last_toc_index = -1
            #Contain the last extracted text
            self.last_extracted_text = ""

    ##########################################################
    # Public methods
    ##########################################################

    # Redefining parent methods

    @property
    def page_num(self) -> int:
        """

        Return
        -------------------
        The number of pages of this PDF file
        """
        self.__page_num = len( self.pdf )
        return self.__page_num

    ##################################################

    @page_num.setter
    def page_num(self, value_i: int) -> None:
        raise Exception("The page number cannot be modified")

    ##################################################

    # Other public methods

    def get_toc(self) -> list:
        """

        Return
        -------------------
        (list) The table of content of this pdf
        """
        return self.toc

    ##################################################

    def get_section_by_heading(self, heading_i: str, first_occurrance_i: bool = True) -> int:
        """
        Search for the section with heading i in its title
        
        heading_i: (str) The string that shall be included in the 
                         heading of the searched sections

        first_occurrance_i: (bool) if False, the method does not return
                            the first occurrance that contains heading_i 
                            but, the one with the lowest heading level

        Return
        -------------------
        toc_index_o: (int) the indexes of the section in the TOC.
        """
        logger.info(f"Searching for section with heading '{heading_i}'")
        toc_index_o = -1
        indexes = self.__get_toc_entries_by_title(heading_i)

        #Check if at least an entry has been found 
        if(len(indexes) > 0):

            if(first_occurrance_i):
                toc_index_o = indexes [0]
            else:
                sub_toc = []
                sub_toc_sorted = None

                for i in indexes:
                    sub_toc.append( ( i, self.toc[i] ) )

                sub_toc_sorted = self.__sort_toc_entries_by_heading(sub_toc, heading_i)
                toc_index_o = sub_toc_sorted[0][0]

            logger.info(f"Section found: '{self.toc[toc_index_o][1]}'")
        else:
            raise DocumentException(f"No section with heading '{heading_i}' found")

        self.last_toc_index = toc_index_o
        return toc_index_o

    ##################################################

    def get_section_pages(self, section_toc_index_i: int) -> dict:
        """
        Return all the pages that belong to the given section 
        i.e. which heading level is < to the one of the given section.

        section_toc_index_i: (int) The index of the
                             section TOC entry

        Return
        -------------------
        section_frame_o: (dict) A dictionary containing the TOC entries information
                         {'start': {'toc_index', 'page'}, 'end': {...} }
                         Notice that the 'page' is the value in TOC - 1.
        """

        start_toc_entry = self.__get_toc_entry(section_toc_index_i)
        section_frame_o = {
            'start':
            {
                'index': section_toc_index_i,
                'page': int(start_toc_entry[2]) - 1, # TOC has a 1 offset
            },
            'end': None
        }
        logger.info(f"Retrieving pages for section index {section_toc_index_i} ('{start_toc_entry[1]}')")

        start_index = section_toc_index_i
        start_level = int( start_toc_entry[0] )
        end_index = -1 # At the beginning, it is used as "not found" flag

        # External loop: find the starting section
        for curr_idx, curr_entry in enumerate(self.toc[start_index + 1: ], start = start_index + 1):

            # End of section found
            if ( curr_entry[0] <= start_level ):
                end_index = curr_idx
                break

        if(end_index > -1):
            section_frame_o['end'] = {
                'index': end_index,
                'page': int(self.__get_toc_entry(end_index)[2]) - 1, # TOC has a 1 offset
            }
        else:
            raise DocumentException(f"The research of section {section_toc_index_i} has failed")
            

        logger.info(f"Section frame retrieved: {section_frame_o}")
        return section_frame_o

    ##################################################

    def get_section_text(self, section_frame_i: dict, fine_trimming_i: bool = False) -> str:
        """
        Get the text content of a pages frame

        section_frame_i: (dict) the output of search_by_title(.)

        fine_trimming_i: (bool) if true, the method calls private sub-rutines 
                         to better clean the extracted text. Default is False.

        Return
        -------------------
        pages_text_o: (str) the text content of the pages frame.
                      It may be correctly empty.
        """

        page_text_o = ""
        pages_text_list = []

        # Section extremes
        start_page = section_frame_i['start']['page']
        start_index = section_frame_i['start']['index']
        end_page = section_frame_i['end']['page']
        end_index = section_frame_i['end']['index']

        # Strings to compare
        sec_title_plain = str( self.toc[start_index][1] )
        sec_title_norm = normalize_string( sec_title_plain )
        next_sec_title_norm = normalize_string( str(self.toc[end_index][1] ) )

        # Indexes to navigate the TOC
        curr_index = start_index # Starting from the first item
        prev_page = -1 # First previous page set to -1 to skip the check

        logger.info(f"Extracting text from pages {start_page} to {end_page}")

        while( curr_index <= end_index ):

            try:
                curr_item = self.toc[curr_index]
                curr_page = curr_item[2] - 1 # TOC pages have 1 offset

                # Skip heading on the same page
                if( prev_page == curr_page ):
                    curr_index += 1 
                    continue

                curr_lines = self.__get_page_text ( curr_page )

                # Case: this is the fist page, the text before the heading (included)
                # shall be removed
                if(curr_page == start_page):
                    curr_lines = remove_text_lines(curr_lines, sec_title_norm)

                # Case: last page. Remove all the text after the next heading (included)
                if (curr_page == end_page):
                    curr_lines = remove_text_lines(curr_lines, next_sec_title_norm, True)

                # Remove shorter lines (it is supposed they are page numbers
                # and other stuffs like that)
                if(fine_trimming_i):
                    curr_lines = remove_short_lines(curr_lines)

            except DocumentException as e:
                logger.error(f"Error extracting text from page {curr_page}: {e}")
                curr_lines = []
            except ValueError as e:
                logger.error(f"Error trimming text from page {curr_page}: {e}")
            finally:
                # Add these lines to the result
                pages_text_list.append( "".join( curr_lines ) )
                # Increment the indexes
                prev_page = curr_page
                curr_index += 1

        logger.info(f"Text extraction completed. Retrieved {len(pages_text_list)} parts.")

        if(len(pages_text_list) > 0):
            page_text_o = page_text_o.join(pages_text_list)
            self.last_extracted_text = page_text_o
            return page_text_o 
        else:
            raise DocumentException(f"Error: Unable to retrieve text from the section '{section_frame_i}'")

    ##################################################

    def get_section_text_by_heading(self, heading_title_i: str) -> tuple[str, str] | str:
        """
        This method embeds the functionalities of
        - get_section_by_heading
        - get_ section pages
        - get_ section_text togheter.
        It uses get_section_by_heading in the manner of returning the section with the lowest heading level.
        It uses get_ section text with the fine trimmings enabled.
        
        heading_title_i: (str) the key-word that shall be present
                        in the section title

        Return
        -------------------
        pages_text_o: (tuple) (section _heading_o, pages_text_o), the title 
                      and the text content of the section, if found.
                      None otherwise.
        """

        logger.info(f"Getting section text by heading: '{heading_title_i}'")
        pages_text_o = ""
        section_heading_o = ""

        try:
            sec = self.get_section_by_heading(heading_title_i, first_occurrance_i = False)
            section_heading_o = self.toc[sec][1]
            sec_frame = self.get_section_pages(sec)
            pages_text_o = self.get_section_text(sec_frame, fine_trimming_i = True)

        except (DocumentException, ValueError) as e:
            logger.error(f"Error getting section text by heading: {e}")
            # Error return
            return ""
        else:
            self.last_extracted_text = pages_text_o
            message = f"{heading_title_i} found in file {self.file_name} in [{sec_frame['start']['page'] + 1}, {sec_frame['end']['page'] + 1}]"
            logging.info(message)
            # Successfully return
            return (section_heading_o, pages_text_o)

    ##################################################

    def save_last_extracted_text(self, output_file_path_i: str) -> str:
        """
        Save the last extracted text to a txt file.

        output_file_path_i: (str) Path of the output text file.

        Return
        -------------------
        output_file_path_i: (str) The same output path in input.
        """

        if(not self.last_extracted_text):
            raise DocumentException("No extracted text available. Call get_section_text or get_section_text_by_heading first.")

        output_dir = os.path.dirname(output_file_path_i)
        if(output_dir != ""):
            os.makedirs(output_dir, exist_ok = True)

        with open(output_file_path_i, "w", encoding = "utf-8") as txt_file:
            txt_file.write(self.last_extracted_text)

        logger.info(f"Last extracted text successfully saved to {output_file_path_i}")
        return output_file_path_i

    ##################################################

    @staticmethod
    def formtat_toc(toc_i: list) -> str:
        """
        Format the table of contents to be displayed in a user-friendly way.

        toc_i: (list) The table of contents to format.

        Return
        -------------------
        toc_o: (str) The formatted table of contents.
        """
        toc_o = ""
        for toc_entry in toc_i:
            toc_o += f"[ Level {toc_entry[0]}, Heading: {toc_entry[1]}, Page {toc_entry[2]} ]\n"
        return toc_o

    ##################################################

    @staticmethod
    def get_all_pdf_documents(dir_path_i: str) -> list['PDFDocument']:
        """
        Search for all PDF documents in a given directory,
        instantiate a PDFDocument for each, and return them.

        dir_path_i: (str) The path of the directory

        Return
        -------------------
        (list) a list of PDFDocument instances
        """
        pdf_docs = []
        all_docs = Document.get_all_documents(dir_path_i)
        
        for doc_path in all_docs:
            if doc_path.lower().endswith('.pdf'):
                try:
                    pdf_doc = PDFDocument(doc_path)
                    pdf_docs.append(pdf_doc)
                except Exception as e:
                    logger.error(f"Failed to load {doc_path}: {e}")
                    
        return pdf_docs

    ##########################################################
    # Private methods
    ##########################################################

    def __get_toc_entry(self, toc_index_i: int) -> list:
        if( toc_index_i < 0 or toc_index_i >= len(self.toc)):
            raise DocumentException(f"Invalid TOC index {toc_index_i}")
        return self.toc[toc_index_i]

    ##################################################

    def __get_page_text(self, page_number_i: int) -> list[str]:
        if(page_number_i < 0 or page_number_i >= self.page_num): 
            raise ValueError(f"Invalid page number {page_number_i}")
        return self.pdf[page_number_i].get_text("text").splitlines(True) # True -› keep line breaks

    ##################################################

    def __get_toc_entries_by_title(self, heading_i: str) -> list[int]:

        correspondences = []
        heading_norm = normalize_string(heading_i)
        for idx, item in enumerate(self.toc):
            if( heading_norm in normalize_string(str( item[1] ) ) ):
                correspondences.append(idx)
        
        return correspondences

    ##################################################

    def __sort_toc_entries_by_heading(self, toc_entries_i: list, searched_heading_i: str) -> list:

        searched_heading_norm = normalize_string(searched_heading_i)

        def sort_func(toc_item):
            heading_level = toc_item[1][0]
            title_norm = normalize_string(str(toc_item[1][1]))
            heading_pos = title_norm.find(searched_heading_norm)

            # Keep non-matching titles at the end if they ever reach this sorter.
            if (heading_pos < 0):
                heading_pos = len(title_norm)

            return (heading_level, heading_pos)

        return sorted( toc_entries_i, key = sort_func )

####################################################################################################

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="[%(name)s :  %(levelname)s] %(message)s")
    pdf = PDFDocument('/Users/calogeroforte/Local_database/UPF_Handout.pdf')
    pdf.get_section_text_by_heading("Intro")
    pdf.save_last_extracted_text('/Users/calogeroforte/Local_database/introduction.txt')
    


