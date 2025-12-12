#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import re
import json
import os
from datetime import datetime

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

def parse_table_improved(main_table):
    """Улучшенный парсинг таблицы"""
    lots = []
    rows = main_table.find_all('tr')
    
    for row in rows:
        # Пропускаем заголовки
        if row.find('th'):
            continue
            
        cells = row.find_all('td')
        if len(cells) < 4:
            continue
            
        # Пытаемся извлечь данные по индексам ячеек
        try:
            # Ячейка с названием (обычно первая или вторая)
            name_cell = cells[1] if len(cells[1].get_text(strip=True)) > 10 else cells[0]
            name = name_cell.get_text(strip=True)
            
            # Ищем ссылку
            link = ""
            link_elem = name_cell.find('a', href=True)
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
            
            # Ищем цену (обычно одна из последних ячеек)
            price_text = ""
            for cell in cells[-3:]:  # Проверяем последние 3 ячейки
                text = cell.get_text(strip=True)
                if re.search(r'\d[\d\s\.]*руб', text, re.I):
                    price_text = text
                    break
            
            # Ищем регион
            region = ""
            for cell in cells:
                text = cell.get_text(strip=True)
                if re.search(r'[А-Я][а-я]+\s*(обл|край|респ|г\.|область)', text):
                    region = text
                    break
            
            if name and price_text:
                price = parse_price(price_text)
                if price > 0:
                    lot = {
                        'name': name,
                        'region': region,
                        'price': price,
                        'link': link,
                        'price_text': price_text
                    }
                    
                    # Проверка на дубликаты
                    if not any(l['name'] == name and abs(l['price'] - price) < 0.01 for l in lots):
                        lots.append(lot)
                        
        except (IndexError, AttributeError):
            continue
    
    return lots

def parse_multiple_pages(base_url, pages=3):
    """Парсит несколько страниц"""
    all_lots = []
    
    for page in range(1, pages + 1):
        print(f"\n📄 Парсинг страницы {page}...")
        
        url = f"{base_url}&page={page}" if "?" in base_url else f"{base_url}?page={page}"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')
            
            if len(tables) > 1:
                main_table = tables[1]
                page_lots = parse_table_improved(main_table)
                all_lots.extend(page_lots)
                print(f"✅ Страница {page}: найдено {len(page_lots)} лотов")
                
        except Exception as e:
            print(f"⚠️ Ошибка на странице {page}: {e}")
            continue
    
    # Удаляем дубликаты
    unique_lots = []
    seen = set()
    for lot in all_lots:
        identifier = (lot['name'][:50], round(lot['price'], 2))
        if identifier not in seen:
            seen.add(identifier)
            unique_lots.append(lot)
    
    return unique_lots

def save_results_to_file(lots, filename="results.json"):
    """Сохраняет результаты в JSON файл"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "total_lots": len(lots),
        "lots": lots
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Результаты сохранены в {filename}")

def save_results_to_csv(lots, filename="results.csv"):
    """Сохраняет результаты в CSV файл"""
    import csv
    
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Номер', 'Название', 'Цена', 'Регион', 'Ссылка'])
        
        for i, lot in enumerate(lots, 1):
            writer.writerow([
                i,
                lot['name'][:100],  # Ограничиваем длину
                lot['price'],
                lot['region'],
                lot['link']
            ])
    
    print(f"💾 Результаты сохранены в {filename}")

def main():
    print("🔍 ПАРСЕР РЕАЛЬНОГО САЙТА Torgi.org")
    print("=" * 50)
    
    url = "https://torgi.org/index.php?class=Auction&action=List&mod=Open&AuctionType=All"
    
    try:
        # Выбор количества страниц
        print("\n📋 СКОЛЬКО СТРАНИЦ ПАРСИТЬ?")
        print("1. Одна страница (быстро)")
        print("2. Несколько страниц (больше данных)")
        
        choice = input("Ваш выбор (1/2): ").strip()
        
        if choice == "2":
            pages_input = input("Сколько страниц парсить? (1-10, по умолчанию 3): ").strip()
            pages = 3  # по умолчанию
            if pages_input:
                try:
                    pages = int(pages_input)
                    if pages < 1:
                        pages = 1
                    elif pages > 10:
                        pages = 10
                except ValueError:
                    print("⚠️ Некорректный ввод, использую 3 страницы")
                    pages = 3
            
            lots = parse_multiple_pages(url, pages)
        else:
            lots = parse_multiple_pages(url, 1)
        
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
            
            # Сохранение результатов
            save_choice = input("\n💾 Сохранить результаты в файл? (y/n): ").strip().lower()
            if save_choice == 'y':
                save_results_to_file(sorted_lots, "torgi_results.json")
                save_results_to_csv(sorted_lots, "torgi_results.csv")
                print("✅ Результаты сохранены в torgi_results.json и torgi_results.csv")
            
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
                    for i, lot in enumerate(filtered_lots, 1):
                        print(f"{i}. {lot['price']:,.2f} руб - {lot['name'][:70]}...")
                    
                    # Сохранение отфильтрованных результатов
                    save_filtered = input("\n💾 Сохранить отфильтрованные результаты? (y/n): ").strip().lower()
                    if save_filtered == 'y':
                        save_results_to_file(filtered_lots, "torgi_filtered.json")
                        save_results_to_csv(filtered_lots, "torgi_filtered.csv")
                        print("✅ Отфильтрованные результаты сохранены")
                else:
                    print("❌ Нет лотов в указанном диапазоне цен")
                    
            except ValueError:
                print("❌ Ошибка ввода цен")
                
        else:
            print("❌ Не удалось найти лоты в таблицах")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
    except KeyboardInterrupt:
        print("\n\n👋 Программа прервана пользователем")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main()
