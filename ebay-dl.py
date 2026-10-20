#!/usr/bin/python3
'''
Download eBay search results and save the listings as JSON (or CSV).

Usage:
    python ebay-dl.py --search "garden tools"
    python ebay-dl.py --search "garden tools" --pages-dir practice-pages
    python ebay-dl.py --search "garden tools" --csv
'''
import argparse
import csv
import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

NUM_PAGES = 10
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0 Safari/537.36'
    ),
}
FIELDS = ['name', 'price', 'status', 'shipping', 'free_returns', 'items_sold']


def parse_cents(text):
    '''
    Return the first dollar amount in `text` as an int number of cents,
    or None if `text` contains no amount.

    >>> parse_cents('$11.95')
    1195
    >>> parse_cents('$12.50 to $18.00')
    1250
    >>> parse_cents('+$4.25 shipping')
    425
    >>> parse_cents('$1,234.00')
    123400
    >>> parse_cents('$7')
    700
    >>> parse_cents('Free shipping') is None
    True
    '''
    match = re.search(r'\$\s*([\d,]+)(?:\.(\d{1,2}))?', text)
    if match is None:
        return None
    dollars = int(match.group(1).replace(',', ''))
    cents = int((match.group(2) or '0').ljust(2, '0'))
    return dollars * 100 + cents


def parse_shipping(text):
    '''
    Return the shipping cost in cents: 0 for free shipping, None if unknown.

    >>> parse_shipping('Free shipping')
    0
    >>> parse_shipping('$4.25 shipping')
    425
    >>> parse_shipping('Shipping not specified') is None
    True
    '''
    if 'free' in text.lower():
        return 0
    return parse_cents(text)


def parse_items_sold(text):
    '''
    Return the number of items sold as an int, or None if not stated.

    >>> parse_items_sold('3 sold')
    3
    >>> parse_items_sold('1,234 sold')
    1234
    >>> parse_items_sold('Almost gone') is None
    True
    '''
    match = re.search(r'([\d,]+)\+?\s+sold', text)
    if match is None:
        return None
    return int(match.group(1).replace(',', ''))


def tag_text(item, selector):
    '''
    Return the stripped text of the first tag matching `selector` inside
    `item`, or None if there is no match.

    >>> item = BeautifulSoup('<li><span class="a"> hi </span></li>', 'html.parser')
    >>> tag_text(item, '.a')
    'hi'
    >>> tag_text(item, '.b') is None
    True
    '''
    tag = item.select_one(selector)
    if tag is None:
        return None
    return tag.text.strip()


def extract_items(html):
    '''
    Return a list of dicts, one per listing (`.s-item`) in `html`.
    A field that a listing does not show is set to None.

    >>> html = (
    ...     '<li class="s-item"><div class="s-item__title">Trowel</div>'
    ...     '<span class="s-item__price">$11.95</span>'
    ...     '<span class="SECONDARY_INFO">Brand New</span>'
    ...     '<span class="s-item__shipping">Free shipping</span>'
    ...     '<span class="s-item__free-returns">Free returns</span>'
    ...     '<span class="s-item__hotness">3 sold</span></li>'
    ...     '<li class="s-item"><div class="s-item__title">Seeds</div></li>'
    ... )
    >>> items = extract_items(html)
    >>> items[0]
    {'name': 'Trowel', 'price': 1195, 'status': 'Brand New', 'shipping': 0, 'free_returns': True, 'items_sold': 3}
    >>> items[1]
    {'name': 'Seeds', 'price': None, 'status': None, 'shipping': None, 'free_returns': None, 'items_sold': None}
    '''
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for listing in soup.select('.s-item'):
        name = tag_text(listing, '.s-item__title')
        price = tag_text(listing, '.s-item__price')
        status = tag_text(listing, '.SECONDARY_INFO')
        shipping = tag_text(listing, '.s-item__shipping, .s-item__logisticsCost')
        returns = tag_text(listing, '.s-item__free-returns')
        sold = tag_text(listing, '.s-item__hotness, .s-item__quantitySold')

        items.append({
            'name': name,
            'price': parse_cents(price) if price is not None else None,
            'status': status,
            'shipping': parse_shipping(shipping) if shipping is not None else None,
            'free_returns': ('free returns' in returns.lower()) if returns is not None else None,
            'items_sold': parse_items_sold(sold) if sold is not None else None,
        })
    return items


EBAY_SEARCH_URL = 'https://www.ebay.com/sch/i.html'


def download_pages(search_term):
    '''
    Yield the HTML of the first NUM_PAGES result pages from eBay.
    Stop early if eBay blocks the request or returns no listings.
    '''
    for page_number in range(1, NUM_PAGES + 1):
        params = {'_nkw': search_term, '_pgn': page_number}
        print(f'downloading page {page_number} for {search_term!r}')
        try:
            response = requests.get(
                EBAY_SEARCH_URL,
                params=params,
                headers=HEADERS,
                timeout=10,
            )
        except requests.RequestException as error:
            print(f'stopping: request failed: {error}', file=sys.stderr)
            return

        status_code = getattr(response, 'status_code', 200)
        if status_code != 200:
            print(f'stopping: HTTP {status_code}; eBay may be blocking automated '
                  'requests. Try --pages-dir practice-pages to use the fixtures.',
                  file=sys.stderr)
            return
        html = response.text
        if 'Pardon Our Interruption' in html or 's-item' not in html:
            print('stopping: eBay returned a robot check or no listings; '
                  'try --pages-dir practice-pages to use the fixtures.',
                  file=sys.stderr)
            return
        yield html

        if page_number < NUM_PAGES:
            time.sleep(1)


def read_pages(pages_dir):
    '''Yield the HTML of page-1.html through page-10.html in `pages_dir`.'''
    for page_number in range(1, NUM_PAGES + 1):
        path = os.path.join(pages_dir, f'page-{page_number}.html')
        with open(path, encoding='utf-8') as f:
            yield f.read()


def save_json(items, filename):
    '''Save `items` as a JSON list.'''
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2)


def save_csv(items, filename):
    '''Save `items` as a CSV file with one row per listing.'''
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(items)


def main():
    parser = argparse.ArgumentParser(
        description='Download eBay search results and save them as JSON.')
    parser.add_argument('search_term', nargs='?',
                        help='search term (positional form, for compatibility)')
    parser.add_argument('--search', dest='search_option',
                        help='the term to search eBay for')
    parser.add_argument('--pages-dir',
                        help='read page-1.html ... page-10.html from this folder '
                             'instead of downloading from eBay')
    parser.add_argument('--csv', action='store_true',
                        help='save a CSV file instead of JSON')
    args = parser.parse_args()
    search_term = args.search_option or args.search_term
    if not search_term:
        parser.error('provide a search term, for example --search "garden tools"')
    if args.search_option and args.search_term:
        parser.error('provide the search term either positionally or with --search, not both')

    if args.pages_dir:
        pages = read_pages(args.pages_dir)
    else:
        pages = download_pages(search_term)

    items = []
    for page_number, html in enumerate(pages, start=1):
        page_items = extract_items(html)
        print(f'page {page_number}: {len(page_items)} listings')
        items.extend(page_items)

    if args.csv:
        filename = f'{search_term}.csv'
        save_csv(items, filename)
    else:
        filename = f'{search_term}.json'
        save_json(items, filename)
    print(f'saved {len(items)} listings to {filename}')


if __name__ == '__main__':
    main()
