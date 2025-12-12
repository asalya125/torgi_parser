#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import re

def parse_price(price_text):
    """Преобразует текст цены в число"""
    if not price_text:
        return 0
    clean_text = re.sub(r'[^\d.]', '', price_text.replace(',', '.'))
    parts = clean_text.split('.')
    if len(parts) > 1:
        clean_text = parts[0] + '.' + ''.join(parts[1:])
    try:
        return float(clean_text) if clean_text else 0
    except ValueError:
        print(f"⚠️ Ошибка преобразования цены: '{price_text}' -> '{clean_text}'")
        return 0

def main():
    print("🔍 ПАРСЕР РЕАЛЬНОГО САЙТА Torgi.org")
    print("=" * 50)
    
    url = "https://torgi.org/index.php?class=Auction&action=List&mod=Open&AuctionType=All"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        print("✅ Страница успешно загружена!")
        
        lots = []
        
        print("🔍 Анализируем все строки таблицы...")
        tables = soup.find_all('table')
        print(f"📊 Найдено таблиц: {len(tables)}")
        
        if len(tables) > 1:
            main_table = tables[1]
            rows = main_table.find_all('tr')
            print(f"📋 Найдено строк в основной таблице: {len(rows)}")
            
            for i, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                
                if len(cells) > 5:
                    price_text = ""
                    name = ""
                    region = ""
                    link = ""
                    
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        
                        if re.search(r'\d[\d\s]*\.?\d*\.?\d*\s*руб', cell_text, re.I):
                            price_text = cell_text
                        
                        elif len(cell_text) > 30 and not price_text and not re.search(r'\d{2}-\d{2}-\d{4}', cell_text):
                            name = cell_text
                            link_elem = cell.find('a', href=True)
                            if link_elem:
                                link_href = link_elem.get('href')
                                if link_href:
                                    if link_href.startswith('/'):
                                        link = 'https://torgi.org' + link_href
                                    elif link_href.startswith('?'):
                                        link = 'https://torgi.org/index.php' + link_href
                                    elif link_href.startswith('index.php'):
                                        link = 'https://torgi.org/' + link_href
                                    else:
                                        link = link_href
                        
                        elif len(cell_text) < 30 and re.search(r'[А-Я][а-я]+\s*обл|г\.|Респ', cell_text):
                            region = cell_text
                    
                    if price_text and name:
                        price = parse_price(price_text)
                        if price > 0:
                            lot = {
                                'name': name,
                                'region': region,
                                'price': price,
                                'link': link,
                                'price_text': price_text
                            }
                            
                            if not any(l['name'] == name and l['price'] == price for l in lots):
                                lots.append(lot)
                                print(f"✅ Лот {len(lots)}: {price:,.2f} руб - {name[:50]}...")
        
        if lots:
            sorted_lots = sorted(lots, key=lambda x: x['price'], reverse=True)
            
            print(f"\n📊 РЕАЛЬНЫЕ ЛОТЫ С САЙТА: Найдено {len(sorted_lots)} лотов")
            print("=" * 100)
            
            for i, lot in enumerate(sorted_lots, 1):
                print(f"{i:2d}. 💰 {lot['price']:12,.2f} руб")
                if lot['region']:
                    print(f"    📍 {lot['region']}")
                print(f"    🏷  {lot['name'][:80]}...")
                if lot['link']:
                    print(f"    🔗 {lot['link']}")
                print("-" * 100)
            
            print("\n🎯 ФИЛЬТРАЦИЯ ПО ЦЕНЕ")
            try:
                min_input = input("Минимальная цена (руб, Enter - пропустить): ").strip()
                max_input = input("Максимальная цена (руб, Enter - пропустить): ").strip()
                
                min_price = float(min_input) if min_input else None
                max_price = float(max_input) if max_input else None
                
                filtered_lots = []
                for lot in sorted_lots:
                    if min_price and lot['price'] < min_price:
                        continue
                    if max_price and lot['price'] > max_price:
                        continue
                    filtered_lots.append(lot)
                
                if filtered_lots:
                    print(f"\n🔍 ОТФИЛЬТРОВАНО ЛОТОВ: {len(filtered_lots)}")
                    print("=" * 100)
                    for i, lot in enumerate(filtered_lots, 1):
                        print(f"{i}. 💰 {lot['price']:,.2f} руб")
                        if lot['region']:
                            print(f"   📍 {lot['region']}")
                        print(f"   🏷  {lot['name'][:70]}...")
                        if lot['link']:
                            print(f"   🔗 {lot['link']}")
                        print("-" * 100)
                else:
                    print("❌ Нет лотов в указанном диапазоне цен")
                    
            except ValueError:
                print("❌ Ошибка ввода цен")
                
        else:
            print("❌ Не удалось найти лоты в таблицах")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main()
