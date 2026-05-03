from typing import Generator
from document import Document

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

    def add_document(self, document_i: Document):
        """
        Set the list of documents.

        value: (list[Document] | None) The list of documents to set
        """
        if isinstance(document_i, Document):
            self.__documents.append(document_i)
        else:
            raise ValueError("The document passed is not an instance of Document class")

    ##################################################

    def __iter__(self):
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