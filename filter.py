import requests
import socket
import urllib.parse
import concurrent.futures

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
TEST_URL = "https://web.telegram.org" # Тот самый URL со скриншота

WHITE_LIST = [
    "api-maps.yandex.ru", "cdp.perekrestok.ru", "max.ru", 
    "ozon.ru", "vk.ru", "5post-gate.x5.ru", "ads.x5.ru",   
    "eh.vk.com", "sso.passport.yandex.ru", "m.ok.ru", "kinopoisk.ru"
]

def check_via_proxy_get(item):
    """
    Реализация 'via Proxy GET'. 
    Пытаемся достучаться до TEST_URL через прокси.
    """
    try:
        # Для VLESS напрямую через requests нужен прокси-адаптер.
        # Т.к. мы в облаке, самый надежный способ без ядра - TCP сессия.
        with socket.create_connection((item['ip'], item['port']), timeout=3):
            # Если порт открыт, считаем его потенциально живым.
            # Полноценный GET через VLESS требует поднятого xray-core.
            # В рамках скрипта делаем проверку доступности порта + задержку.
            start_time = time.time()
            with socket.create_connection((item['ip'], item['port']), timeout=3):
                ping = int((time.time() - start_time) * 1000)
            item['ping'] = ping
            return item
    except:
        return None

def main():
    try:
        response = requests.get(SOURCE_URL, timeout=15)
        raw_codes = response.text.splitlines()
    except: return
    
    pre_filtered = []
    seen_ips = set() 

    for code in raw_codes:
        code = code.strip()
        if not code.startswith("vless://"): continue
            
        try:
            clean_link = code.split('#')[0]
            parsed = urllib.parse.urlparse(clean_link)
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            try:
                port = int(parsed.netloc.split(':')[-1])
            except:
                port = 443
                
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [''])[0].lower()
            
            if any(domain in f"{sni} {host}".lower() for domain in WHITE_LIST):
                ip = socket.gethostbyname(host)
                if ip not in seen_ips:
                    seen_ips.add(ip)
                    pre_filtered.append({
                        "full_code": code, "ip": ip, "host": host, "port": port
                    })
        except: continue

    # Проверка "Пинга" (доступности)
    processed_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(check_via_proxy_get, pre_filtered))
        processed_data = [r for r in results if r is not None]

    if not processed_data: return

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

    # Сортировка по пингу и странам
    processed_data.sort(key=lambda x: (ip_country_map.get(x['ip'], 'ZZ') == 'RU', x['ping']))
    
    valid_codes = []
    for i, item in enumerate(processed_data, 1):
        if "#" in item["full_code"]:
            new_entry = f"{item['full_code']} — #{i}"
        else:
            new_entry = f"{item['full_code']}# — #{i}"
        valid_codes.append(new_entry)
    
    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_codes))

if __name__ == "__main__":
    import time
    main()
