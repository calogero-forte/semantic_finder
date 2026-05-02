import os
from abc import ABC, abstractmethod

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

    ##########################################################
    # Public methods
    ##########################################################

    @property
    @abstractmethod
    def page_num(self):
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
    def page_num(self, value):
        """
        Set the current page number.

        value: (int) The page number to set
        """
        pass

    ##################################################

    def get_file_name(self):
        """

        Return
        -------------------
        (str) the name of this file
        """
        return self.__file_name

    ##################################################

    @staticmethod
    def extract_filename(path_i):
        """
        Extract the filename from a given Document path.

        pdf_path_i: (str) The path (absolute or relative) 
                    of the file

        Return
        -------------------
        (str) the name of this PDF
        """
        return os.path.basename(path_i)

    ##################################################

    @staticmethod
    def get_all_documents(dir_path_i):
        """
        Search for all documents in a given directory.

        dir_path_i: (str) The path of the directory

        Return
        -------------------
        (list) a list of file paths found in the directory
        """
        if not os.path.isdir(dir_path_i):
            return []
            
        docs = []
        for file in os.listdir(dir_path_i):
            full_path = os.path.join(dir_path_i, file)
            if os.path.isfile(full_path):
                docs.append(full_path)
        return docs