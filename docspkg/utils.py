"""
License Statement & Module Information
======================================

This code is provided as open-source software and has been developed as part of the 
Master in Applied Artificial Intelligence postgraduate course, for the Python Programming topic.

The purpose of this application is to serve as a Model Context Protocol (MCP) server, 
providing a Large Language Model (LLM) the capability to access and retrieve 
information from local documents to answer related queries.

- Program Name: Semantic Finder
- Module Name: utils.py
- Revision: 1.0
- Author: Calogero Forte
- Affiliation: University of Palermo
- Development Date: May 2026
"""

"""
This module containts a set of util functions
which use is common across all package
"""

import re

def normalize_string(string_i: str) -> str:
        """
        Remove white spaces, dots and heading numbers;
        put all in lower case.

        string_i: (str) The string to manipulate

        Return
        -------------------
        (str) The clean string
        """
        clean_string = re.sub( r'^\d+(?:\.\d+)*', '', string_i )
        clean_string = re.sub( r'[.\s]', '', clean_string )
        return clean_string.lower()

##################################################

def remove_text_lines(text_lines_i: list[str], line_break_i: str, forward_i: bool = False) -> list[str]:
    """
    Remove text lines based on a line break string.

    text_lines_i: (list[str]) The text lines to process
    line_break_i: (str) The line break string to search for
    forward_i: (bool) Whether to remove lines before or after the break

    Return
    -------------------
    (list[str]) The processed text lines
    """

    line_break_norm = normalize_string(line_break_i)
    i = 0
    while( line_break_norm not in normalize_string( text_lines_i[i] ) ):
        i += 1
        if( i == len( text_lines_i) ):
            break

    if(i < 0 or i >= len (text_lines_i) ):
        raise ValueError(f"Line index {i} is out of range")

    if( not forward_i ):
        return text_lines_i[ i + 1 : ]
    else:   
        return text_lines_i[ : i ]

##################################################

def remove_short_lines(text_lines_i: list[str], min_words_for_line_i: int = 3) -> list[str]:
    """
    Remove lines that are shorter than a minimum number of words.

    text_lines_i: (list[str]) The text lines to process
    min_words_for_line_i: (int) Minimum words required for a line

    Return
    -------------------
    (list[str]) The processed text lines
    """
    text_lines_o = []
    for s in text_lines_i:
        if( len( s.split() ) >= min_words_for_line_i ):
            text_lines_o.append(s)
    return text_lines_o