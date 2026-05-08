import requests
import socket
import urllib.parse

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"

# Твой белый список доменов
WHITE_LIST = [
    "api-maps.yandex.ru", 
    "cdp.perekrestok.ru", 
    "max.ru", 
    "ozon.ru", 
    "vk.ru", 
    "5post-gate.x5.ru", 
    "ads.x5.ru"
]

def main():
    try:
        response = requests.get(SOURCE_URL, timeout=15)
        raw_codes = response.text.splitlines()
    except: return
    
    processed_data = []
    seen_ips = set() 

    for code in raw_codes:
        code = code.strip()
        if not code.startswith("vless://"): continue
            
        try:
            # Разбираем ссылку, чтобы вытащить SNI/Host для фильтрации
            # Но саму оригинальную ссылку (code) сохраняем целиком!
            parts = code.split('#')
            clean_link = parts[0]
            original_name = parts[1] if len(parts) > 1 else ""
            
            parsed = urllib.parse.urlparse(clean_link)
            params = urllib.parse.parse_qs(parsed.query)
            
            sni = params.get('sni', [''])[0].lower()
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            
            search_area = f"{sni} {host}".lower()
            
            # Проверяем вхождение доменов из белого списка
            if any(domain in search_area for domain in WHITE_LIST):
                try:
                    ip = socket.gethostbyname(host)
                    if ip in seen_ips: continue 
                    
                    seen_ips.add(ip)
                    processed_data.append({
                        "full_code": code,
                        "ip": ip,
                        "host": host
                    })
                except: continue
        except: continue

    if not processed_data: return

    # Пакетная проверка стран (только для сортировки, в название не пишем!)
    ip_country_map = {}
    ips_to_check = [item["ip"] for item in processed_data]
    for i in range(0, len(ips_to_check), 100):
        batch = ips_to_check[i:i+100]
        try:
            res = requests.post("http://ip-api.com/batch?fields=query,countryCode,isp", json=batch, timeout=10).json()
            for item in res:
                query = item.get("query")
                country = item.get("countryCode", "ZZ")
                isp = item.get("isp", "").lower()
                if any(x in isp for x in ['yandex', 'vdsina', 'selectel', 'x5', 'mail.ru', 'vkontakte']):
                    country = "RU"
                ip_country_map[query] = country
        except: pass

    # Сортировка: Зарубежные сверху, РФ снизу
    processed_data.sort(key=lambda x: (ip_country_map.get(x['ip'], 'ZZ') == 'RU', x['host']))
    
    valid_codes = []
    for i, item in enumerate(processed_data, 1):
        # Оставляем оригинальный код как есть и просто добавляем номер в конец
        # Если в коде уже был #название, добавится " — #1"
        # Если не было, создастся "# — #1"
        if "#" in item["full_code"]:
            new_entry = f"{item['full_code']} — #{i}"
        else:
            new_entry = f"{item['full_code']}# — #{i}"
        
        valid_codes.append(new_entry)
    
    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_codes))

if __name__ == "__main__":
    main()
