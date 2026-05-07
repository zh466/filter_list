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
        my_codes = requests.get(SOURCE_URL, timeout=15).text.splitlines()
    except: return
    
    servers_data = []
    unique_ips = set()

    # 1. Собираем уникальные серверы
    for code in my_codes:
        if not code.startswith("vless://"): continue
        try:
            parsed = urllib.parse.urlparse(code)
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [''])[0].lower()
            
            if not (sni.endswith('.ru') or host.endswith('.ru')): continue

            ip = socket.gethostbyname(host)
            if ip in unique_ips or ip in blocked_data: continue
            
            unique_ips.add(ip)
            servers_data.append({
                "code": code.split('#')[0],
                "sni": sni if sni else host,
                "ip": ip
            })
        except: continue

    # 2. Мгновенная и точная проверка стран (сразу пачкой до 100 IP за раз)
    ip_country_map = {}
    ip_list = list(unique_ips)
    
    for i in range(0, len(ip_list), 100):
        batch = ip_list[i:i+100]
        try:
            # Используем самый точный сервис для VPN-адресов
            res = requests.post("http://ip-api.com/batch?fields=query,countryCode", json=batch, timeout=10).json()
            for item in res:
                if "query" in item and "countryCode" in item:
                    ip_country_map[item["query"]] = item["countryCode"]
        except:
            pass

    # 3. Присваиваем страны и сортируем
    for server in servers_data:
        server["country"] = ip_country_map.get(server["ip"], "ZZ")

    # Сортировка: Зарубежные сверху, Россия (RU) — всегда внизу
    servers_data.sort(key=lambda x: (x['country'] == 'RU', x['country'], x['sni']))
    
    # 4. Формируем ссылки с ЭМОДЗИ
    valid_codes = []
    for i, item in enumerate(servers_data, 1):
        flag = get_flag(item['country'])
        # Формат: 🇳🇱 yandex.ru — #1
        new_name = f"{flag} {item['sni']} — #{i}" 
        
        safe_name = urllib.parse.quote(new_name)
        valid_codes.append(f"{item['code']}#{safe_name}")
    
    with open("valid_vless.txt", "w") as f:
        f.write("\n".join(valid_codes))

if __name__ == "__main__":
    main()
