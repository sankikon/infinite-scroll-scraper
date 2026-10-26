# Infinite-scroll store scraper

A lot of online stores don't use pages anymore. Products load as you scroll,
so a simple scraper that downloads the HTML only sees the first few. This one
opens a real browser with Playwright, keeps scrolling until nothing new shows
up, and then saves every product to a spreadsheet.

I built it against webscraper.io's practice store, which is made for this kind
of testing and behaves like a real shop.

## What you get

A CSV with one row per product: category, full product name, price as a
number (so you can sort and sum it in Excel), description, review count, star
rating and a link to the product page.

Example: `ejemplo_productos.csv` has all 147 products across 3 categories. I
checked it against the site: no duplicates, no missing names, and the laptop
count (117) matches the store.

## How to run it

```bash
pip install playwright
python -m playwright install chromium
python tienda_scraper.py
```

| Option | What it does |
|---|---|
| `--salida` | Output file name (default `productos.csv`) |
| `--ver` | Opens the browser so you can watch it work |
| `--test` | Runs the built-in check |

## A few details

- It finds the categories by itself, so new ones get picked up without
  touching the code.
- Product names on the listing are cut short. It reads the full name from the
  link instead.
- If something fails halfway, it still saves what it already collected.
- It waits between scrolls instead of hammering the site.
