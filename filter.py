import requests
import socket
import urllib.parse
import time

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"

WHITE_LIST = [
    "api-maps.yandex.ru", 
    "cdp.perekrestok.ru", 
    "max.ru", 
    "ozon.ru", 
    "vk.ru", 
    "5post-gate.x5.ru", 
    "ads.x5.ru"
]

def check_tcp_port(host, port, timeout=2):
    """Проверяет, отвечает ли порт сервера (аналог пинга для прокси)."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except:
        return False

def main():
    try:
        response = requests.get(SOURCE_URL, timeout=15)
        raw_codes = response.text.splitlines()
    except: return
    
    processed_data = []
    seen_ips = set() 

    print(f"Начинаю проверку {len(raw_codes)} строк...")

    for code in raw_codes:
        code = code.strip()
        if not code.startswith("vless://"): continue
            
        try:
            parts = code.split('#')
            clean_link = parts[0]
            
            parsed = urllib.parse.urlparse(clean_link)
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            # Достаем порт, если его нет — по умолчанию 443
            try:
                port = int(parsed.netloc.split(':')[-1])
            except:
                port = 443
                
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [''])[0].lower()
            
            search_area = f"{sni} {host}".lower()
            
            if any(domain in search_area for domain in WHITE_LIST):
                try:
                    ip = socket.gethostbyname(host)
                    if ip in seen_ips: continue 
                    
                    # ПРОВЕРКА ДОСТУПНОСТИ (ПИНГ)
                    if not check_tcp_port(ip, port):
                        print(f"Сервер {host} не отвечает, пропускаю.")
                        continue

                    seen_ips.add(ip)
                    processed_data.append({
                        "full_code": code,
                        "ip": ip,
                        "host": host
                    })
                except: continue
        except: continue

    if not processed_data:
        print("Живых серверов не найдено.")
        return

    # Пакетная проверка стран для сортировки
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
        if "#" in item["full_code"]:
            new_entry = f"{item['full_code']} — #{i}"
        else:
            new_entry = f"{item['full_code']}# — #{i}"
        valid_codes.append(new_entry)
    
    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_codes))
    print(f"Готово! Сохранено {len(valid_codes)} живых серверов.")

if __name__ == "__main__":
    main()
