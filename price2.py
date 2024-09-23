import asyncio
from playwright.async_api import async_playwright
import csv
from datetime import datetime

# Ключевые товары для поиска
search_queries = {
    "копье": "https://www.wildberries.ru/catalog/0/search.aspx?search=копье",
    "дуршлаг": "https://www.ozon.ru/search/?text=дуршлаг",
    "красные носки": "https://market.yandex.ru/search?text=красные%20носки",
    "леска для спиннинга": "https://www.wildberries.ru/catalog/0/search.aspx?search=леска%20для%20спиннинга"
}

# Функция для сохранения данных в CSV
def save_to_csv(data):
    with open("market_prices.csv", mode="a", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(data)

# Функция парсинга цен
async def fetch_lowest_price(playwright, product_name, url):
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto(url)

    # Поиск товаров и их цен
    prices = []
    
    if "wildberries" in url:
        items_selector = ".product-card"
        price_selector = ".price-block__final-price"
    elif "ozon" in url:
        items_selector = ".ui-product-card"
        price_selector = ".ui-c5.ui-c8"
    elif "yandex" in url:
        items_selector = ".n-snippet-card"
        price_selector = ".price .price_value"

    # Получаем карточки товаров
    items = await page.query_selector_all(items_selector)
    
    for item in items:
        try:
            price_text = await item.query_selector(price_selector)
            if price_text:
                price = float(await price_text.inner_text().replace('₽', '').replace(' ', ''))
                link = await item.get_attribute("href") if "wildberries" in url else url
                prices.append((price, product_name, link))
        except Exception as e:
            print(f"Ошибка при парсинге товара: {e}")

    # Сохраняем товар с наименьшей ценой
    if prices:
        lowest_price = min(prices, key=lambda x: x[0])
        save_to_csv([lowest_price[1], lowest_price[2], lowest_price[0], datetime.now().isoformat()])
        print(f"{lowest_price[1]} - {lowest_price[0]} ₽ по ссылке: {lowest_price[2]}")

    await browser.close()

# Основная функция для запуска Playwright
async def monitor_prices():
    async with async_playwright() as playwright:
        tasks = []
        for product_name, url in search_queries.items():
            task = asyncio.ensure_future(fetch_lowest_price(playwright, product_name, url))
            tasks.append(task)
        await asyncio.gather(*tasks)

# Запуск
asyncio.run(monitor_prices())