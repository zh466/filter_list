import requests
import socket
import ssl
import urllib.parse
import concurrent.futures
import time

# Источник и список доменов
SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
WHITE_LIST = [
    "api-maps.yandex.ru", "cdp.perekrestok.ru", "max.ru", 
    "ozon.ru", "vk.ru", "5post-gate.x5.ru", "ads.x5.ru",   
    "eh.vk.com", "sso.passport.yandex.ru", "m.ok.ru", "kinopoisk.ru"
]

def extreme_ping_check(item):
    """Строгая проверка: TCP + SSL + ALPN + Write тест"""
    try:
        start_time = time.time()
        # 1. TCP коннект
        sock = socket.create_connection((item['ip'], item['port']), timeout=4)
        
        # 2. Настройка SSL с поддержкой протоколов VLESS
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_alpn_protocols(['h2', 'http/1.1'])
        
        with context.wrap_socket(sock, server_hostname=item['sni']) as ssock:
            ssock.settimeout(2.0)
            try:
                # 3. Тестовая запись (проверка, что сокет реально готов к данным)
                ssock.write(b'\x00')
            except:
                return None # Сервер-заглушка сбросит соединение здесь
                
            item['ping'] = int((time.time() - start_time) * 1000)
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
            # Отделяем ссылку от старого имени
            parts = code.split('#')
            clean_link = parts[0]
            
            parsed = urllib.parse.urlparse(clean_link)
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            try:
                port = int(parsed.netloc.split(':')[-1])
            except: port = 443
                
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [host])[0].lower()
            
            # Фильтр по белому списку доменов
            if any(domain in f"{sni} {host}".lower() for domain in WHITE_LIST):
                ip = socket.gethostbyname(host)
                if ip not in seen_ips:
                    seen_ips.add(ip)
                    pre_filtered.append({
                        "full_code": clean_link, 
                        "ip": ip, 
                        "port": port, 
                        "sni": sni
                    })
        except: continue

    # Запускаем проверку в 20 потоков
    processed_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(extreme_ping_check, pre_filtered))
        processed_data = [r for r in results if r is not None]

    if not processed_data: return

    # Запрос стран для правильной сортировки (RU вниз)
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
                # Если провайдер явно российский, помечаем как RU
                if any(x in isp for x in ['yandex', 'vdsina', 'selectel', 'x5', 'mail.ru', 'vkontakte', 'beeline', 'mts']):
                    country = "RU"
                ip_country_map[query] = country
        except: pass

    # Сортировка: Зарубежные -> РФ. Внутри групп — по пингу.
    processed_data.sort(key=lambda x: (ip_country_map.get(x['ip'], 'ZZ') == 'RU', x['ping']))
    
    # Сборка финального файла с простой нумерацией
    valid_codes = []
    for i, item in enumerate(processed_data, 1):
        valid_codes.append(f"{item['full_code']}# — #{i}")
    
    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_codes))

if __name__ == "__main__":
    main() 
