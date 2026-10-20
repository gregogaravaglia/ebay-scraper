"""Small unit tests for the eBay scraper's parsing helpers."""
import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('ebay-dl.py')
loader = importlib.machinery.SourceFileLoader('ebay_dl', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
ebay_dl = importlib.util.module_from_spec(spec)
loader.exec_module(ebay_dl)


class ParsingTests(unittest.TestCase):
    def test_parse_cents(self):
        self.assertEqual(ebay_dl.parse_cents('$11.95'), 1195)
        self.assertEqual(ebay_dl.parse_cents('$12.50 to $18.00'), 1250)
        self.assertEqual(ebay_dl.parse_cents('$1,234.00'), 123400)
        self.assertIsNone(ebay_dl.parse_cents('Price unavailable'))

    def test_parse_shipping(self):
        self.assertEqual(ebay_dl.parse_shipping('Free shipping'), 0)
        self.assertEqual(ebay_dl.parse_shipping('$4.25 shipping'), 425)
        self.assertIsNone(ebay_dl.parse_shipping('Shipping not specified'))

    def test_parse_items_sold(self):
        self.assertEqual(ebay_dl.parse_items_sold('1,234 sold'), 1234)
        self.assertIsNone(ebay_dl.parse_items_sold('Almost gone'))

    def test_missing_listing_fields(self):
        items = ebay_dl.extract_items(
            '<li class="s-item"><div class="s-item__title">Seeds</div></li>'
        )
        self.assertEqual(items, [{
            'name': 'Seeds', 'price': None, 'status': None,
            'shipping': None, 'free_returns': None, 'items_sold': None,
        }])

    def test_all_practice_pages_are_readable(self):
        pages_dir = Path(__file__).with_name('practice-pages')
        pages = list(ebay_dl.read_pages(str(pages_dir)))
        self.assertEqual(len(pages), 10)
        items = []
        for page in pages:
            items.extend(ebay_dl.extract_items(page))
        self.assertEqual(len(items), 30)
        self.assertTrue(any(item['name'] == 'Garden trowel 10' for item in items))


if __name__ == '__main__':
    unittest.main()
