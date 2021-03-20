"""
This is a module for checking links in the Mathe für Nicht-Freaks Wikibooks
project.

Ran as a standalone script this creates prompts for the information it needs in
order to check the links.
"""

import os.path
import sys
import csv
import getopt

from bs4 import BeautifulSoup

from util import site_caching, bookinfo

EXCLUDED_HEADING_IDS = (
    'Buchanfänge',
    'Über_das_Projekt'
)


def check_links_on_page(page, page_dict):
    """This taks a BeautifulSoup object and checks if all links on it exist."""
    # Create a copy of the page as we are going to remove stuff from it
    page = BeautifulSoup(str(page), 'html.parser')
    # Remove Serlo head since it contains parts of the sitemap
    # We don't wan't to check the links in there. They all exist or provide
    # unnecessary redlink warnings.
    serlo_header = page.find(id='serlo-header')
    if serlo_header is not None:
        serlo_header.extract()
    links, redlinks = bookinfo.find_links(page, warn_redlinks=True)
    bad_links = [{'target': link, 'id': '', 'reason': 'Redlink'}
                 for link in redlinks]
    for link in links:
        # Ignore external links
        if not link.startswith('/'):
            continue
        # Split page link and location on page
        link_split = link.split('#', 1)
        # Ignore links not pointing to an id
        if len(link_split) == 1:
            continue
        (linked_page, linked_id) = link_split
        if linked_page not in page_dict:
            print('Unknown link target: {}'.format(linked_page))
            bad_links.append({
                'target': linked_page,
                'id': linked_id,
                'reason': 'Link not in cache'
            })
            continue
        target_page = page_dict[linked_page]
        if not target_page.find(id=linked_id):
            print('Found a link from "{}" to "{}". On the target page the id "{}" is not present.'.
                  format(page.title.get_text(), target_page.title.get_text(),
                         linked_id))
            bad_links.append({
                'target': linked_page,
                'id': linked_id,
                'reason': 'ID not present on target page'
            })
    return bad_links


def yes_no_prompt(prompt, default=None):
    """
    Asks Yes/No Question. If default is not None an empty answer will yield
    this as a return value.
    """
    if default is None:
        prompt += " [y/n] "
    elif default:
        prompt += " [Y/n] "
    else:
        prompt += " [y/N] "
    while True:
        answer = input(prompt)
        if answer in ("y", "Y"):
            return True
        if answer in ("n", "N"):
            return True
        if answer == "" and default is not None:
            return default
        print("Please answer 'y' or 'n'.")


def check_book(pages_of_book, pages):
    """Check all pages of the given article list"""
    bad_book_links = []
    for page in pages_of_book:
        # Ignore MediaWiki speacial pages
        if page.startswith('/wiki/Spezial:'):
            continue
        if page in pages:
            bad_links = check_links_on_page(pages[page], pages)
            for link_data in bad_links:
                bad_book_links.append({'source': page, **link_data})
        else:
            print('Couldn\'t find page "{}" inside the page cache.'.format(page))
            bad_book_links.append({
                'source': page,
                'target': '',
                'id': '',
                'reason': 'Page not in cache'
            })
    return bad_book_links


def main():
    """Main function when called from command line."""
    def postprocess_page(string):
        return BeautifulSoup(string, "html.parser")

    (opts_list, args) = getopt.getopt(sys.argv[1:], 'c:rlb:')
    opts = dict(opts_list)

    if '-c' in opts and os.path.isfile(opts['-c']) and '-r' not in opts:
        (books, pages) = site_caching.read_cached_data(
            page_postprocessor=postprocess_page)
    else:
        books = bookinfo.fetch_article_list()
        pages = {}
        for book in books:
            pages = {
                **pages,
                **bookinfo.fetch_pages_from_list(
                    books[book], page_postprocessor=postprocess_page)
            }
        if '-c' in opts:
            site_caching.cache_page_data(books, pages, cache=opts['-c'])

    if '-l' in opts:
        print("The follwing books are available:")
        for book in books:
            print(book)
        sys.exit(0)

    books_to_check = []
    if '-b' in opts:
        if opts['-b'] in books:
            books_to_check = [opts['-b']]
        else:
            print('The book "{}" is not available.'.format(opts['-b']))
            sys.exit(1)
    else:
        books_to_check = books.keys()

    logfile = 'bad_log.csv'
    if len(args) >= 1:
        logfile = args[0]
    with open(logfile, 'w', newline='') as csv_logfile:
        fieldnames = ['book', 'source', 'target', 'id', 'reason']
        log_writer = csv.DictWriter(csv_logfile, fieldnames=fieldnames)
        log_writer.writeheader()
        for book in books_to_check:
            print('Checking book "{}":'.format(book))
            bad_data = check_book(books[book], pages)
            for datum in bad_data:
                log_writer.writerow({'book': book, **datum})


if __name__ == '__main__':
    main()
