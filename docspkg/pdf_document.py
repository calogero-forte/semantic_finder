"""
License Statement & Module Information
======================================

This code is provided as open-source software and has been developed as part of the 
Master in Applied Artificial Intelligence postgraduate course, for the Python Programming topic.

The purpose of this application is to serve as a Model Context Protocol (MCP) server, 
providing a Large Language Model (LLM) the capability to access and retrieve 
information from local documents to answer related queries.

- Program Name: Semantic Finder
- Module Name: pdf_document.py
- Revision: 1.0
- Author: Calogero Forte
- Affiliation: University of Palermo
- Development Date: May 2026
"""

from .document import Document, DocumentException
from .toc_document import TocDocument
from .utils import *
import pymupdf 
import os 
import re
import logging

logger = logging.getLogger(__name__)

class PDFDocument(Document, TocDocument):
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
            self.__toc = self.pdf.get_toc(simple = True)

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

    @property
    def toc(self) -> list:
        """

        Return
        -------------------
        (list) The table of content of this pdf
        """
        if(self.__toc == None or len(self.__toc) == 0):
            raise DocumentException("The table of contents is empty.")
        return self.__toc
    
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
            except (ValueError, IndexError) as e:
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

    def __get_page_text(self, page_number_i: int) -> list[str]:
        if(page_number_i < 0 or page_number_i >= self.page_num): 
            raise ValueError(f"Invalid page number {page_number_i}")
        return self.pdf[page_number_i].get_text("text").splitlines(True) # True -› keep line breaks

####################################################################################################

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="[%(name)s :  %(levelname)s] %(message)s")
    pdf = PDFDocument('/Users/calogeroforte/Local_database/UPF_Handout.pdf')
    pdf.get_section_text_by_heading("Intro")
    pdf.save_last_extracted_text('/Users/calogeroforte/Local_database/introduction.txt')
    


