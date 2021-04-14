"""
Module for analysing the double usage of content in the Mathe für Nicht-Freaks
project.

When run as a standalone script this performs all necessary steps for analysing
all passages which are used multiple times across the Mathe für Nicht-Freaks
project.
"""

import os
import sys
import getopt
import re

from util import bookinfo, site_caching


def extract_sections(string):
    """
    Find all <section> environments and return their content as string array.
    """
    section_regex = re.compile('<section begin(.+?)<section end', re.DOTALL)
    return [match.group(1) for match in section_regex.finditer(string)]


def count_sections(string):
    """
    Count the number of <section> environments in string.
    """
    return string.count("<section begin")


def detect_sections(string):
    """
    For debugging: Find first occurence of <section in string
    and distance to next occurrence
    """
    first = string.find("<section")
    if first != -1:
        print(first, string[first+1:].find("<section"))
    return []


def extract_section_usages(string):
    """
    Extract all usages of sections from string and return the names of the used
    sections (with multiplicities) as list.
    """
    usage_regex = re.compile('{{#lst:(.+?)}}')
    usage_substrings = []
    for match in usage_regex.finditer(string):
        usage_substrings.append(match.group(1))
    return usage_substrings


def count_section_usages(string):
    """
    Count how often the substring {{#lst: occurs
    """
    return string.count("{{#lst:")


def main():
    """Main program body."""
    bookinfo.EXCLUDED_HEADING_IDS = (
        'Buchanfänge',
        'Über_das_Projekt',
        'Mitmachen_für_(Nicht-)Freaks',
    )
    (opts_list, _) = getopt.getopt(sys.argv[1:], 'c:r')
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

    sections = []
    usages = []
    section_counter = 0
    usage_counter = 0
    for page in pages:
        sections.extend(extract_sections(pages[page]))
        section_counter += count_sections(pages[page])
        usages.extend(extract_section_usages(pages[page]))
        usage_counter += count_section_usages(pages[page])

    found_sections = list(sections)
    found_usages = list(usages)
    print("Found {} marked sections with {} overall usages".format(
        section_counter, usage_counter))

    os.makedirs("out", exist_ok=True)
    with open("out/sections.txt", 'w+') as file:
        file.write('\n\n ______________________________________\n\n'.join(
            found_sections))
    with open("out/section_usages.txt", 'w+') as file:
        file.write(str(usage_counter) + ' usages found:\n\n')
        file.write('\n'.join(found_usages))


if __name__ == '__main__':
    main()
