"""
Module for finding the TeX macros used in the Mathe für Nicht-Freaks project.

When run as a standalone script this performs all necessary steps for finding
all TeX macros in the Mathe für Nicht-Freaks project.
"""

import os
import sys
import getopt
import re

from util import bookinfo, site_caching


def extract_math_substrings(string):
    """
    Find all <math> environments and return their content as string array.
    """
    math_regex = re.compile('<math>(.+?)</math>')
    math_substrings = []
    for match in math_regex.finditer(string):
        math_substrings.append(match.group(1))
    return math_substrings


def extract_tex_macros(string):
    """
    Find all TeX macros in the given string and return them as a string array.
    The given string is assumed to be the content of a <math> environment.
    """
    math_regex = re.compile('\\\\(?:(?:begin|end){[^}]+}|[@A-Za-z]+|.)')
    return math_regex.findall(string)


def extract_tex_macros_of_page(string):
    """
    Find all TeX macros in the given string and return them as a string array.
    Assume that all TeX macros are still contained in <math> environments which
    have to be identified first. Thus this can handle the raw page source.
    """
    tex_macros = []
    for match_env in extract_math_substrings(string):
        tex_macros.extend(extract_tex_macros(match_env))
    return tex_macros


def main():
    """Main program body."""
    (opts_list, _) = getopt.getopt(sys.argv[1:], 'c:ro:')
    opts = dict(opts_list)

    if '-c' in opts and os.path.isfile(opts['-c']) and '-r' not in opts:
        (books, pages) = site_caching.read_cached_data(cache=opts['-c'])
    else:
        books = bookinfo.fetch_article_list()
        pages = {}
        for book in books:
            page_content = bookinfo.fetch_pages_from_list(
                books[book], action='raw',
                page_postprocessor=lambda byte_string:
                byte_string.decode('utf-8'))
            pages = {
                **pages,
                **page_content
            }
        if '-c' in opts:
            site_caching.cache_page_data(books, pages, cache=opts['-c'])

    tex_macros = []
    for page in pages:
        tex_macros.extend(extract_tex_macros_of_page(pages[page]))

    discovered_macros = list(set(tex_macros))
    discovered_macros.sort()

    print('\n'.join(discovered_macros))

    if '-o' in opts:
        with open(opts['-o'], 'w') as filehandle:
            filehandle.write('\n'.join(discovered_macros))


if __name__ == '__main__':
    main()
