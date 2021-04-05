"""
Module for collection information about the articles which are in the book of
the Mathe für Nicht-Freaks project.
"""
import urllib.request
import re

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
    If warn_redlinks=True this prints a warning message for every redlink it
    encounters.
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
            if redlink_regex.search(link) and warn_redlinks and \
               not link_ignore_regex.search(link):
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
        # Get all headings, the first result is dropped as it is the table of
        # contents.
        # The last result is a mysterious "Navigationsmenü".
        headings = sitemap.find_all('h2')[1:-1]
        books = {}
        for i in range(len(headings)):
            if is_heading_excluded(headings[i]):
                continue
            # fetch content of heading
            books[get_heading_id(headings[i])] = clean_urls(find_links(
                BeautifulSoup(get_content_till_tag(headings[i], headings[i+1]),
                              'html.parser'),
                False)[0])
        return books


def fetch_pages_from_list(page_urls, action='view',
                          page_postprocessor=lambda byte_string: byte_string):
    """
    Fetch every url in page_urls which corresponds to an article on the Mathe
    für Nicht-Freaks project, process the response with page_postprocessor and
    store the results in a dictionary, which is indexed by the urls.
    Return the filled dictionary.
    """
    page_content = {}
    existing_article_regex = re.compile(
        '^/wiki/((?:Mathe_f%C3%BCr_Nicht-Freaks|Serlo):.+)$')
    url_scheme = 'https://de.wikibooks.org/w/index.php?title={}&action={}'
    for url in page_urls:
        # Ignore external links:
        match = existing_article_regex.match(url)
        if match is None:
            continue
        print("Fetching: {}".format(url))
        with urllib.request.urlopen(
                url_scheme.format(match.group(1), action)) as response:
            page = page_postprocessor(response.read())
            page_content[url] = page
    return page_content
