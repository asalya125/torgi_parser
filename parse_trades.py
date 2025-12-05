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
        
        # Находим все таблицы
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
                        
                        # Поиск цены
                        if re.search(r'\d[\d\s]*\.?\d*\.?\d*\s*руб', cell_text, re.I):
                            price_text = cell_text
                        
                        # Поиск названия и ссылки
                        elif len(cell_text) > 30 and not price_text and not re.search(r'\d{2}-\d{2}-\d{4}', cell_text):
                            name = cell_text
                            
                            # 🔧 ИСПРАВЛЕНИЕ: Ищем ссылку в ячейке
                            link_elem = cell.find('a', href=True)
                            if link_elem:
                                link_href = link_elem.get('href')
                                # 🔧 ИСПРАВЛЕНИЕ: Правильно обрабатываем ссылки
                                if link_href:
                                    if link_href.startswith('/'):
                                        # Относительная ссылка: /index.php?...
                                        link = 'https://torgi.org' + link_href
                                    elif link_href.startswith('?'):
                                        # Ссылка начинается с ?: ?class=...
                                        link = 'https://torgi.org/index.php' + link_href
                                    elif link_href.startswith('index.php'):
                                        # Ссылка начинается с index.php?...
                                        link = 'https://torgi.org/' + link_href
                                    else:
                                        link = link_href
                        
                        # Поиск региона
                        elif len(cell_text) < 30 and re.search(r'[А-Я][а-я]+\s*обл|г\.|Респ', cell_text):
                            region = cell_text
                    
                    # Если нашли и цену и название
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
                            
                            # Проверяем на дубликаты
                            if not any(l['name'] == name and l['price'] == price for l in lots):
                                lots.append(lot)
                                print(f"✅ Лот {len(lots)}: {price:,.2f} руб - {name[:50]}...")
                                # 🔧 ДОПОЛНИТЕЛЬНО: Показываем ссылку для отладки
                                if link:
                                    print(f"   🔗 Ссылка: {link}")
        
        # ... остальной код без изменений ...
