"""
This is a module for checking links in the Mathe für Nicht-Freaks Wikibooks Project

Ran as a standalone script this creates prompts for the information it needs in order
to check the links.
"""

import sqlite3
import urllib.request
import re
import csv

from bs4 import BeautifulSoup

EXCLUDED_HEADING_IDS = (
    'Buchanfänge',
    'Über_das_Projekt'
)

def is_heading_excluded(heading):
    """Check whether a heading should be exluded from processing."""
    for identifier in EXCLUDED_HEADING_IDS:
        if heading.find(id=identifier):
            return True
    return False

def get_content_till_tag(start_tag, end_tag=None):
    """
    Return the html between start_tag and end_tag. The start and end tag are
    excluded from the return string.
    """
    content = ''
    current_tag = start_tag.next_sibling
    while current_tag != end_tag:
        content += str(current_tag)
        current_tag = current_tag.next_sibling
    return content

def get_heading_id(heading):
    """Get the MfNF generated ID belongig to a heading."""
    return heading.find('span', 'mw-headline').get('id')

def clean_urls(url_list):
    """Remove the position on the page the link points to."""
    clean_regex = re.compile('#.*$')
    for i in range(len(url_list)):
        url_list[i] = clean_regex.sub('', url_list[i])
    return url_list

def find_links(bs_obj, warn_redlinks=True):
    """
    Find all href-tags inside the given bs_obj.
    If warn_redlinks=True this prints a warning message for every redlink it encounters.
    """
    # Regex to filter nonexistent pages and edit links
    existence_regex = re.compile('\\?(?:.+&)?action=edit(?:&|$)')
    # Regex to filter nonexistent pages
    redlink_regex = re.compile('\\?(?:.+&)?redlink=1(?:&|$)')
    # Regex to ignore Discussion and User pages
    link_ignore_regex = re.compile('\\?(.+&)?title=(?:Diskussion|Benutzer)')
    link_objects = bs_obj.find_all('a')
    links = []
    redlinks = []
    for link_object in link_objects:
        link = link_object.get('href')
        # Ignore a-tags without a href attribute
        if not link:
            continue
        if existence_regex.search(link):
            if redlink_regex.search(link) and warn_redlinks and not link_ignore_regex.search(link):
                print('Found link pointing to nonexistent page: {}'.format(link))
                redlinks.append(link)
            continue
        links.append(link)
    return links, redlinks

def fetch_article_list():
    """Download the sitemap and extract all links from it"""
    # Retrieve sitemap
    with urllib.request.urlopen(
            'https://de.wikibooks.org/w/index.php?title=Mathe_f%C3%BCr_Nicht-Freaks:_Sitemap') \
            as response:
        sitemap = BeautifulSoup(response.read(), "html.parser")
        # Get all headings, the first result is dropped as it is the table of contents.
        # The last result is a mysterious "Navigationsmenü".
        headings = sitemap.find_all('h2')[1:-1]
        books = {}
        for i in range(len(headings)):
            if is_heading_excluded(headings[i]):
                continue
            # fetch content of heading
            books[get_heading_id(headings[i])] = clean_urls(find_links(
                BeautifulSoup(get_content_till_tag(headings[i], headings[i+1]), 'html.parser'),
                False)[0])
        return books

def fetch_pages_from_list(page_urls):
    """
    Fetch every url in page_urls and store the results as BeautifulSoup object in a
    dictionary, which is indexed by the urls.
    """
    page_content = {}
    external_link_regex = re.compile('^https?://')
    for url in page_urls:
        # Ignore external links:
        if external_link_regex.match(url):
            continue
        print("Fetchning: {}".format(url))
        with urllib.request.urlopen('https://de.wikibooks.org{}'.format(url)) as response:
            page = BeautifulSoup(response.read(), "html.parser")
            page_content[url] = page
    return page_content

def check_links_on_page(page, page_dict):
    """This taks a BeautifulSoup object and checks if all links on it exist."""
    # Create a copy of the page as we are going to remove stuff from it
    page = BeautifulSoup(str(page), 'html.parser')
    # Remove Serlo head since it contains parts of the sitemap
    # We don't wan't to check the links in there. They all exist or provide unnecessary
    # redlink warnings.
    serlo_header = page.find(id='serlo-header')
    if serlo_header is not None:
        serlo_header.extract()
    links, redlinks = find_links(page, warn_redlinks=True)
    bad_links = [{'target': link, 'id': '', 'reason': 'Redlink'} for link in redlinks]
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
                  format(page.title.get_text(), target_page.title.get_text(), linked_id))
            bad_links.append({
                'target': linked_page,
                'id': linked_id,
                'reason': 'ID not present on target page'
            })
    return bad_links

# Chaching
def reset_cache_db(db_connection):
    """Reset the cache database or set it up if there isn't anything there yet."""
    with db_connection:
        db_connection.execute('DROP TABLE IF EXISTS books')
        db_connection.execute('DROP TABLE IF EXISTS pages')
        db_connection.execute('CREATE TABLE books (name TEXT, page_url TEXT)')
        db_connection.execute(
            'CREATE TABLE pages (url TEXT PRIMARY KEY ON CONFLICT REPLACE, content TEXT)')

def cache_page_data(books, page_urls):
    """
    Save the given books and page_urls in the cache database.
    WARNING: This destroys all other cached data.
    """
    db_connection = sqlite3.connect('cache.db')
    reset_cache_db(db_connection)
    # insert books into cache
    with db_connection:
        for book in books:
            for page in books[book]:
                db_connection.execute('INSERT INTO books(name, page_url) VALUES (?, ?)',
                                      (book, page))
    # insert pages
    with db_connection:
        for page_url in page_urls:
            db_connection.execute('INSERT INTO pages(url, content) VALUES (?, ?)',
                                  (page_url, str(page_urls[page_url])))
    db_connection.close()

def read_cached_data():
    """
    Load cached books and pages.
    Returns these dictionaries as a pair (books, pages).
    """
    db_connection = sqlite3.connect('cache.db')
    cursor = db_connection.execute('SELECT name, page_url FROM books')
    # Read books
    books = {}
    for row in cursor:
        if row[0] in books:
            books[row[0]].append(row[1])
        else:
            books[row[0]] = [row[1]]
    # Read pages
    cursor = db_connection.execute('SELECT url, content FROM pages')
    pages = {}
    for row in cursor:
        pages[row[0]] = BeautifulSoup(row[1], "html.parser")
    db_connection.close()
    return (books, pages)

def yes_no_prompt(prompt, default=None):
    """
    Asks Yes/No Question. If default is not None an empty answer will yield this as a return value.
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
    if yes_no_prompt("(Re)Build cached data?", False):
        books = fetch_article_list()
        pages = {}
        for book in books:
            pages = {**pages, **fetch_pages_from_list(books[book])}
        cache_page_data(books, pages)
    else:
        (books, pages) = read_cached_data()
    print("We have the following Books to check:")
    for book in books:
        print(book)
    books_to_check = []
    while not books_to_check:
        book_to_check = input("Which book do you want to check? (book name or all) ")
        if book_to_check == 'all':
            books_to_check = books.keys()
        elif book_to_check in books:
            books_to_check = [book_to_check]
        else:
            print('Please choose a book from the list above or all.')

    with open('bad_log.csv', 'w', newline='') as csv_logfile:
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
