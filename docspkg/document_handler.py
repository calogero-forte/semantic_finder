import os
import logging
from typing import Generator
from .document import Document
from .pdf_document import PDFDocument

logger = logging.getLogger(__name__)

class DocumentHandler:
    """
    This class manages a list of Documents, providing functionality 
    to iterate, filter, and access them.
    """

    def __init__(self, documents: list[Document] | None = None):
        """
        Initialize a DocumentHandler.

        documents: (list[Document] | None) Initial list of documents. 
                   If None, an empty list is created.

        Return
        -------------------
        A DocumentHandler
        """
        self.__documents = documents if documents is not None else []

    ##########################################################
    # Public methods
    ##########################################################

    def get_all_documents(self) -> list[Document]:
        """
        Get the current list of documents.

        Return
        -------------------
        (list[Document]) the list of managed documents
        """
        return self.__documents

    ##################################################

    def add_document(self, document_i: Document) -> None:
        """
        Add a document to the list.

        document_i: (Document) The document to add

        Return
        -------------------
        None
        """
        if isinstance(document_i, Document):
            self.__documents.append(document_i)
        else:
            raise ValueError("The document passed is not an instance of Document class")

    ##################################################

    def clear_documents(self) -> None:
        """
        Clear the list of managed documents.

        Return
        -------------------
        None
        """
        self.__documents.clear()

    ##################################################

    def __iter__(self) -> Generator[Document, None, None]:
        """
        Return an iterator over the documents.

        Return
        -------------------
        (iterator) an iterator for the document list
        """
        return iter(self.__documents)

    ##################################################

    def __len__(self) -> int:
        """
        Get the number of documents in the handler.

        Return
        -------------------
        (int) the number of documents
        """
        return len(self.__documents)

    ##################################################

    def filter_documents(self, name_i: str | None = None, extension_i: str | None = None) -> Generator[Document, None, None]:
        """
        A generator that yields documents filtered by name and/or extension.

        name_i: (str | None) A substring to match in the filename
        extension_i: (str | None) The extension to match (e.g. '.pdf', 'docx')

        Return
        -------------------
        (Generator) yields Document objects matching the criteria
        """

        # Clean the passed extension for compatibility with the
        # one stored in Document 
        if extension_i is not None and extension_i.startswith('.'):
            extension_i = extension_i.lstrip('.')

        for doc in self.__documents:
            
            match_name = ( name_i is not None ) and ( name_i in doc.file_name )
            match_ext = ( extension_i is not None ) and ( extension_i == doc.file_extenstion)
            
            if match_name or match_ext:
                yield doc

    ##################################################

    def sync_documents(self, directory_path_i: str) -> None:
        """
        Synchronizes this DocumentHandler with the files
        currently inside directory_path_i

        directory_path_i: (str) The path to sync

        Return
        -------------------
        None
        """
        local_paths = os.path.expanduser(directory_path_i)
        if( not os.path.exists(local_paths) or not os.path.isdir(local_paths) ):
            logger.error( f"{local_paths} is not a directory" )
            return

        current_files = DocumentHandler.get_directory_documents(local_paths)
        
        # Here it would be good to have a timer 
        self.clear_documents()
        
        for file_path in current_files:
            ext = Document.get_file_extension( file_path )
            try:
                if ext == 'pdf':
                    doc = PDFDocument(file_path)
                    self.add_document(doc)
                else:
                    # Add future document handlers here (e.g., txt, docx) using polymorphism
                    logger.debug(f"Document type '{ext}' is not currently supported: {file_path}")
            except Exception as e:
                logger.error(f"Failed to load document {file_path}: {e}")

    ##################################################

    @staticmethod
    def get_directory_documents(dir_path_i: str) -> list[str]:
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

####################################################################################################

if __name__ == '__main__':

    from pdf_document import PDFDocument

    docs = [PDFDocument( '/Users/calogeroforte/Local_database/Lezioni di Teoria dei Segnali.pdf' ), PDFDocument( '/Users/calogeroforte/Local_database/VHDL - Programming by Example.pdf' )]
    dh = DocumentHandler(docs)
    
    print(dh.get_all_documents())

    for d in dh:
        print(d.file_name)

    for d in dh.filter_documents(name_i = 'VHDL'):
        print(d.file_name)

    for d in dh.filter_documents(extension_i = '.pdf'):
        print(d.file_name)