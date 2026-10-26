"""Extrae todos los productos de una tienda con scroll infinito y los guarda en CSV.

Sitio de práctica: https://webscraper.io/test-sites/e-commerce/scroll
(hecho para practicar scraping; los productos cargan con JavaScript al bajar).

Uso:
    python tienda_scraper.py
    python tienda_scraper.py --salida productos.csv --ver
    python tienda_scraper.py --test
"""
import argparse
import csv
import re
import sys
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE = "https://webscraper.io/test-sites/e-commerce/scroll"
CAMPOS = ["Categoría", "Producto", "Precio (USD)", "Descripción", "Reseñas", "Estrellas", "Enlace"]


def a_numero(precio):
    return float(re.sub(r"[^\d.]", "", precio))


def subcategorias(page):
    """Recorre las categorías principales y devuelve las URLs de sus subcategorías."""
    page.goto(BASE)
    principales = page.eval_on_selector_all("a.category-link", "as => as.map(a => a.href)")
    urls = []
    for url in principales:
        page.goto(url)
        urls += page.eval_on_selector_all("a.subcategory-link", "as => as.map(a => a.href)")
    return list(dict.fromkeys(urls))  # sin duplicados, en orden


def bajar_hasta_el_final(page, pausa_ms=1200):
    # baja hasta que dejan de aparecer productos nuevos
    anterior = -1
    while (actual := page.locator(".thumbnail").count()) != anterior:
        anterior = actual
        page.mouse.wheel(0, 20000)
        page.wait_for_timeout(pausa_ms)


def extraer(page, categoria):
    filas = []
    for card in page.locator(".thumbnail").all():
        titulo = card.locator("a.title")
        filas.append({
            "Categoría": categoria,
            "Producto": titulo.get_attribute("title"),  # el texto visible viene recortado
            "Precio (USD)": a_numero(card.locator(".price").inner_text()),
            "Descripción": card.locator(".description").inner_text().strip(),
            "Reseñas": int(card.locator("[itemprop=reviewCount]").inner_text()),
            "Estrellas": card.locator(".ws-icon-star").count(),
            "Enlace": urljoin(BASE, titulo.get_attribute("href")),
        })
    return filas


def guardar_csv(filas, ruta):
    # utf-8-sig: Excel en español abre bien las tildes
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)


def autoprueba():
    assert a_numero("$1,295.99") == 1295.99
    assert a_numero("$24.99") == 24.99
    print("autoprueba OK")


def main():
    p = argparse.ArgumentParser(description="Extrae productos de una tienda con scroll infinito.")
    p.add_argument("--salida", default="productos.csv", help="archivo CSV de salida")
    p.add_argument("--ver", action="store_true", help="abre el navegador visible")
    p.add_argument("--test", action="store_true", help="ejecuta la autoprueba y sale")
    a = p.parse_args()

    if a.test:
        autoprueba()
        return

    filas = []
    with sync_playwright() as pw:
        navegador = pw.chromium.launch(headless=not a.ver)
        page = navegador.new_page()
        try:
            for url in subcategorias(page):
                categoria = url.removeprefix(BASE + "/")
                page.goto(url)
                bajar_hasta_el_final(page)
                nuevas = extraer(page, categoria)
                print(f"{categoria}: {len(nuevas)} productos")
                filas += nuevas
        except Exception as e:
            # guarda lo que ya se extrajo antes de salir
            guardar_csv(filas, a.salida)
            sys.exit(f"Error: {e}. Se guardaron {len(filas)} productos en {a.salida}")
        finally:
            navegador.close()

    guardar_csv(filas, a.salida)
    print(f"Total: {len(filas)} productos guardados en {a.salida}")


if __name__ == "__main__":
    main()
