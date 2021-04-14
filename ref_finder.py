"""
Module for analysing the usage of references in the Mathe für Nicht-Freaks
project.

When run as a standalone script this performs all necessary steps for analysing
all references which are used in the Mathe für Nicht-Freaks project.
"""

from util import bookinfo, content_stats


def main():
    """Main program body."""
    bookinfo.EXCLUDED_HEADING_IDS = (
        'Buchanfänge',
        'Über_das_Projekt',
        'Mitmachen_für_(Nicht-)Freaks',
    )
    (_, pages, _) = bookinfo.book_argument_parser()

    content_stats.basic_analysis('ref', pages, '<ref>(.+?)</ref>')


if __name__ == '__main__':
    main()
