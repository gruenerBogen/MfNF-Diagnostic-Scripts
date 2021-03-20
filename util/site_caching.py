"""
This module contains helper function for caching page-related data.
"""

import sqlite3


def reset_cache_db(db_connection):
    """
    Reset the cache database or set it up if there isn't anything there yet.
    """
    with db_connection:
        db_connection.execute('DROP TABLE IF EXISTS books')
        db_connection.execute('DROP TABLE IF EXISTS pages')
        db_connection.execute('CREATE TABLE books (name TEXT, page_url TEXT)')
        db_connection.execute(
            'CREATE TABLE pages (url TEXT PRIMARY KEY ON CONFLICT REPLACE, ' +
            'content TEXT)')


def cache_page_data(books, page_urls, cache='cache.db'):
    """
    Save the given books and page_urls in the cache database.
    cache is the location of the cache database.
    WARNING: This destroys all other cached data.
    """
    db_connection = sqlite3.connect(cache)
    reset_cache_db(db_connection)
    # insert books into cache
    with db_connection:
        for book in books:
            for page in books[book]:
                db_connection.execute(
                    'INSERT INTO books(name, page_url) VALUES (?, ?)',
                    (book, page))
    # insert pages
    with db_connection:
        for page_url in page_urls:
            db_connection.execute(
                'INSERT INTO pages(url, content) VALUES (?, ?)',
                (page_url, str(page_urls[page_url])))
    db_connection.close()


def read_cached_data(page_postprocessor=lambda string: string,
                     cache='cache.db'):
    """
    Load cached books and pages.
    You can apply page_postprocessor to each string associated to a page.
    You can specify a different cache by changing the cache file.
    Returns these dictionaries as a pair (books, pages).
    """
    db_connection = sqlite3.connect(cache)
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
        pages[row[0]] = page_postprocessor(row[1])
    db_connection.close()
    return (books, pages)
