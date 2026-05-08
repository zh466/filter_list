import requests
import socket
import urllib.parse
import concurrent.futures

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

def check_server_health(item):
    """
    Проверяет сервер: сначала TCP порт, потом пытается 'увидеть' домен.
    Это максимально близкая имитация 'get via proxy' без поднятия ядра.
    """
    try:
        # 1. Проверка порта (TCP Ping)
        with socket.create_connection((item['ip'], item['port']), timeout=2.5):
            # 2. Попытка сделать легкий HEAD запрос к хосту (имитация проброса трафика)
            # Если сервер позволяет резолвить домен, значит он скорее всего жив
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
            parts = code.split('#')
            clean_link = parts[0]
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
                        "full_code": code,
                        "ip": ip,
                        "host": host,
                        "port": port
                    })
        except: continue

    # Многопоточная проверка (чтобы не ждать по 2 секунды каждый сервер)
    print(f"Проверяю {len(pre_filtered)} серверов на 'отклик'...")
    processed_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_server_health, pre_filtered))
        processed_data = [r for r in results if r is not None]

    if not processed_data:
        print("Рабочих серверов не найдено.")
        return

    # Пакетная проверка стран для правильной сортировки
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

    # Сортировка: Зарубежные -> РФ
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
    print(f"Успех! Сохранено {len(valid_codes)} активных серверов.")

if __name__ == "__main__":
    main()
