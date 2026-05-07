import requests
import socket
import urllib.parse

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
BLOCKLIST_URL = "https://antifilter.download/list/ip.txt"

def get_flag(country_code):
    if not country_code or len(country_code) != 2 or country_code == "ZZ":
        return "🌐"
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())

def main():
    try:
        blocked_data = requests.get(BLOCKLIST_URL, timeout=15).text
        # Берем только уникальные строки из твоего файла
        raw_codes = list(dict.fromkeys(requests.get(SOURCE_URL, timeout=15).text.splitlines()))
    except: return
    
    processed_data = []
    ips_to_check = []

    for code in raw_codes:
        if not code.startswith("vless://"): continue
        try:
            # Отрезаем старое название, если оно было
            clean_link = code.split('#')[0]
            parsed = urllib.parse.urlparse(clean_link)
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [''])[0].lower()
            
            # Фильтр по .ru
            if not (sni.endswith('.ru') or host.endswith('.ru')): continue

            ip = socket.gethostbyname(host)
            if ip in blocked_data: continue
            
            # Сохраняем данные, чтобы потом сопоставить с ответом API
            processed_data.append({
                "link": clean_link,
                "sni": sni if sni else host,
                "ip": ip
            })
            ips_to_check.append(ip)
        except: continue

    # Пакетная проверка стран (точно по списку IP)
    ip_country_map = {}
    for i in range(0, len(ips_to_check), 100):
        batch = ips_to_check[i:i+100]
        try:
            res = requests.post("http://ip-api.com/batch?fields=query,countryCode", json=batch, timeout=10).json()
            for item in res:
                ip_country_map[item["query"]] = item.get("countryCode", "ZZ")
        except: pass

    # Сборка финального списка
    final_list = []
    for item in processed_data:
        country = ip_country_map.get(item["ip"], "ZZ")
        final_list.append({
            "link": item["link"],
            "sni": item["sni"],
            "country": country.upper()
        })

    # Сортировка: Сначала НЕ RU, Россия в конце
    final_list.sort(key=lambda x: (x['country'] == 'RU', x['country'], x['sni']))
    
    valid_codes = []
    for i, item in enumerate(final_list, 1):
        flag = get_flag(item['country'])
        # Формируем новое название
        new_name = f"{flag} {item['sni']} — #{i}"
        safe_name = urllib.parse.quote(new_name)
        valid_codes.append(f"{item['link']}#{safe_name}")
    
    with open("valid_vless.txt", "w") as f:
        f.write("\n".join(valid_codes))

if __name__ == "__main__":
    main()
