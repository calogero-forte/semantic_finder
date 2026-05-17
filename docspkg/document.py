"""
License Statement & Module Information
======================================

This code is provided as open-source software and has been developed as part of the 
Master in Applied Artificial Intelligence postgraduate course, for the Python Programming topic.

The purpose of this application is to serve as a Model Context Protocol (MCP) server, 
providing a Large Language Model (LLM) the capability to access and retrieve 
information from local documents to answer related queries.

- Program Name: Semantic Finder
- Module Name: document.py
- Revision: 1.0
- Author: Calogero Forte
- Affiliation: University of Palermo
- Development Date: May 2026
"""

import os
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class Document(ABC):
    """
    This class represents a generic document and provides an interface 
    for managing common document properties like page numbers and paths.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize a Document

        kwargs can contain:
        path_i: (str) The path (absolute or relative) 
                of the document file

        Return
        -------------------
        A Document
        """

        path = kwargs.get('path_i', None)

        if( path != None):
            self.__path = path
            self.__file_name = Document.extract_filename(path)
            self.__page_num = 0
            #Contain the last extracted text
            self.last_extracted_text = ""

    ##########################################################
    # Public methods
    ##########################################################

    @property
    @abstractmethod
    def page_num(self) -> int:
        """
        Get the current page number.

        Return
        -------------------
        (int) the current page number
        """
        pass

    ##################################################

    @page_num.setter
    @abstractmethod
    def page_num(self, value_i: int) -> None:
        """
        Set the current page number.

        value_i: (int) The page number to set

        Return
        -------------------
        None
        """
        pass

    ##################################################

    @property
    def file_name(self) -> str:
        """

        Return
        -------------------
        (str) the name of this file
        """
        return self.__file_name

    ##################################################

    @property
    def file_extenstion(self) -> str:
        """

        Return
        -------------------
        (str) the extension of this file
        """
        return Document.get_file_extension( self.file_name )

    ##################################################

    def save_last_extracted_text(self, output_file_path_i: str) -> str:
        """
        Save the last extracted text to a file.

        output_file_path_i: (str) The path to the output file

        Return
        -------------------
        (str) The path to the output file
        """
        if not self.last_extracted_text:
            raise DocumentException("No extracted text available.")

        output_dir = os.path.dirname(output_file_path_i)
        if output_dir != "":
            os.makedirs(output_dir, exist_ok=True)

        with open(output_file_path_i, "w", encoding="utf-8") as f:
            f.write(self.last_extracted_text)

        logger.info(f"Last extracted text successfully saved to {output_file_path_i}")
        return output_file_path_i

    ##################################################

    @staticmethod
    def extract_filename(path_i: str) -> str:
        """
        Extract the filename from a given Document path.

        path_i: (str) The path (absolute or relative) 
                of the file

        Return
        -------------------
        (str) the name of this PDF
        """
        return os.path.basename(path_i)

    ##################################################

    @staticmethod
    def get_file_extension(file_path_i: str) -> str:
        """
        Retrieve the extension from a file name/path

        file_path_i: (str) The path (absolute or relative) 
                     of the file

        Return
        -------------------
        (str) the extension of this file without the dot
        """
        return file_path_i.lower().split('.')[-1]

####################################################################################################

class DocumentException(Exception):
    """
    Custom exception for Document errors.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
    