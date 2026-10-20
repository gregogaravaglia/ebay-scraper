# eBay Scraper

This project is for [Project 2: Scraping eBay](https://csci40.rtealwitter.com/projects/02_webscraping/project.html). The program searches eBay for a term you provide, reads up to 10 pages of results, and saves the listings to a JSON file. It uses `requests` to download pages and Beautiful Soup to read the HTML.

Each listing includes these fields:

- `name`: the item's title
- `price`: price in cents (if a price range is shown, it uses the first price)
- `status`: the item's condition
- `shipping`: shipping cost in cents; `0` means free shipping
- `free_returns`: whether free returns are offered
- `items_sold`: the number of items sold

If a value is missing from a listing, it is saved as `null`.

## Setup

Install the required packages:

```bash
python -m pip install requests beautifulsoup4
```

## Run a search

To search eBay, run the script with `--search` followed by the search terms in quotation marks:

```bash
python ebay-dl.py --search "garden tools"
```

The script tries to download up to 10 pages and saves the results in `garden tools.json`. eBay may block automated requests or show a robot check. If that happens, the script reports the problem instead of treating the page as search results.

## Use the practice pages

The project also includes 10 local HTML pages for testing. To use those pages rather than sending requests to eBay, add `--pages-dir practice-pages`:

```bash
python ebay-dl.py --search "garden tools" --pages-dir practice-pages
```

The JSON and CSV files included in this repository were created from these practice pages. Because the same practice pages are used for each search term, the three saved searches contain the same listings; the filenames differ. To recreate them, run:

```bash
python ebay-dl.py --search "garden tools" --pages-dir practice-pages
python ebay-dl.py --search "drill press" --pages-dir practice-pages
python ebay-dl.py --search "stuffed animal" --pages-dir practice-pages
```

## CSV output

To save the results as a CSV file instead of JSON, add `--csv`. This works with live searches or the practice pages. For example:

```bash
python ebay-dl.py --search "garden tools" --csv
```

To recreate the three CSV files included here using the practice pages, run:

```bash
python ebay-dl.py --search "garden tools" --pages-dir practice-pages --csv
python ebay-dl.py --search "drill press" --pages-dir practice-pages --csv
python ebay-dl.py --search "stuffed animal" --pages-dir practice-pages --csv
```

## Run the tests

Run the unit tests with:

```bash
python -m unittest -v test_ebay_dl.py
```
