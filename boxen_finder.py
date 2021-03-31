"""
Module for analysing the usage of custom templates used on the Mathe für
Nicht-Freaks project.

When run as a standalone script this performs all necessary steps for analysing
the usage of custom templates on the Mathe für Nicht-Freaks project.
"""

import os
import sys
import getopt
import re

from util import bookinfo, site_caching


def extract_templates(string):
    """
    Find all occurences of custom templates in the given string and return them
    as a string array.
    """
    math_regex = re.compile(
        '{{:Mathe\\s+für\\s+Nicht-Freaks:\\s+Vorlage:[^|\\n]+')
    findings = [s.strip() for s in math_regex.findall(string)]
    return findings


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
        tex_macros.extend(extract_templates(pages[page]))

    discovered_macros = list(set(tex_macros))
    discovered_macros.sort()

    out_text = []
    for box in discovered_macros:
        out_text.append(box + "\t" + str(tex_macros.count(box)))

    print('\n'.join(out_text))

    if '-o' in opts:
        with open(opts['-o'], 'w') as filehandle:
            filehandle.write('\n'.join(out_text))


if __name__ == '__main__':
    main()
