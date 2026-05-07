import requests
import socket
import urllib.parse

# Добавляем случайный параметр, чтобы обойти кэш GitHub при загрузке
SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt?nocache=1"

def get_flag(country_code):
    if not country_code or len(country_code) != 2 or country_code == "ZZ":
        return "🌐"
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())

def main():
    try:
        # Указываем заголовки, чтобы GitHub не отдавал старый файл
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        response = requests.get(SOURCE_URL, headers=headers, timeout=15)
        raw_codes = response.text.splitlines()
    except Exception as e:
        print(f"Ошибка: {e}")
        return
    
    processed_data = []
    ips_to_check = []
    seen_links = set()

    for code in raw_codes:
        code = code.strip()
        if not code.startswith("vless://"): continue
            
        try:
            clean_link = code.split('#')[0]
            if clean_link in seen_links: continue
            
            parsed = urllib.parse.urlparse(clean_link)
            params = urllib.parse.parse_qs(parsed.query)
            
            sni = params.get('sni', [''])[0].lower()
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            display_name = sni if sni else host

            if ".ru" in display_name:
                try:
                    ip = socket.gethostbyname(host)
                    processed_data.append({
                        "link": clean_link,
                        "name": display_name,
                        "ip": ip
                    })
                    ips_to_check.append(ip)
                    seen_links.add(clean_link)
                except: continue
        except: continue

    if not processed_data: return

    # Пакетная проверка стран
    ip_country_map = {}
    for i in range(0, len(ips_to_check), 100):
        batch = ips_to_check[i:i+100]
        try:
            res = requests.post("http://ip-api.com/batch?fields=query,countryCode", json=batch, timeout=10).json()
            for item in res:
                ip_country_map[item["query"]] = item.get("countryCode", "ZZ")
        except: pass

    # Сортировка (Зарубежные -> РФ)
    processed_data.sort(key=lambda x: (ip_country_map.get(x['ip'], 'ZZ') == 'RU', x['name']))
    
    valid_codes = []
    for i, item in enumerate(processed_data, 1):
        country_code = ip_country_map.get(item["ip"], "ZZ")
        flag = get_flag(country_code)
        # Собираем: [Флаг] [SNI] — #[Номер]
        new_name = f"{flag} {item['name']} — #{i}"
        safe_name = urllib.parse.quote(new_name)
        valid_codes.append(f"{item['link']}#{safe_name}")
    
    # Сохраняем результат
    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_codes))

if __name__ == "__main__":
    main()
