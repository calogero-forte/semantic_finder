import logging
from abc import ABC, abstractmethod
from .utils import normalize_string
from .document import DocumentException

logger = logging.getLogger(__name__)

class TocDocument(ABC):

    ##########################################################
    # Public methods
    ##########################################################
    
    @property
    @abstractmethod
    def toc(self) -> list:
        pass

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
        indexes = self._get_toc_entries_by_title(heading_i)

        #Check if at least an entry has been found 
        if(len(indexes) > 0):

            if(first_occurrance_i):
                toc_index_o = indexes [0]
            else:
                sub_toc = []
                sub_toc_sorted = None

                for i in indexes:
                    sub_toc.append( ( i, self.toc[i] ) )

                sub_toc_sorted = self._sort_toc_entries_by_heading(sub_toc, heading_i)
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

        start_toc_entry = self.toc[section_toc_index_i]
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

        for curr_idx, curr_entry in enumerate(self.toc[start_index + 1: ], start = start_index + 1):

            # End of section found
            if ( curr_entry[0] <= start_level ):
                end_index = curr_idx
                break

        if(end_index > -1):
            section_frame_o['end'] = {
                'index': end_index,
                'page': int(self._get_toc_entry(end_index)[2]) - 1, # TOC has a 1 offset
            }
        else:
            raise DocumentException(f"The research of section {section_toc_index_i} has failed")
            

        logger.info(f"Section frame retrieved: {section_frame_o}")
        return section_frame_o

    ##################################################

    @abstractmethod
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

        # Add logic here to extract text from pages 
        pass

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

    ##########################################################
    # Private methods
    ##########################################################

    def _sort_toc_entries_by_heading(self, toc_entries_i: list, searched_heading_i: str) -> list:

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

    ##################################################

    def _get_toc_entry(self, toc_index_i: int) -> list:
        if( toc_index_i < 0 or toc_index_i >= len(self.toc)):
            raise DocumentException(f"Invalid TOC index {toc_index_i}")
        return self.toc[toc_index_i]

    ##################################################

    def _get_toc_entries_by_title(self, heading_i: str) -> list[int]:

        correspondences = []
        heading_norm = normalize_string(heading_i)
        for idx, item in enumerate(self.toc):
            if( heading_norm in normalize_string(str( item[1] ) ) ):
                correspondences.append(idx)
        
        return correspondences