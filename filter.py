import requests
import socket
import ssl
import urllib.parse
import concurrent.futures
import time

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
WHITE_LIST = [
    "api-maps.yandex.ru", "cdp.perekrestok.ru", "max.ru", "ozon.ru", 
    "vk.ru", "5post-gate.x5.ru", "ads.x5.ru", "eh.vk.com", 
    "sso.passport.yandex.ru", "m.ok.ru", "kinopoisk.ru",
    "cloud.mail.ru", "a.wb.ru"
]

def real_get_check(item):
    """Имитация 'via Proxy GET' через реальный HTTP-запрос"""
    try:
        start_time = time.time()
        sock = socket.create_connection((item['ip'], item['port']), timeout=5)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with context.wrap_socket(sock, server_hostname=item['sni']) as ssock:
            ssock.settimeout(3.0)
            # Формируем запрос, как в мобильном приложении
            http_request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {item['sni']}\r\n"
                f"User-Agent: Mozilla/5.0\r\n"
                f"Connection: close\r\n\r\n"
            )
            ssock.sendall(http_request.encode())
            response = ssock.recv(1024)
            if b"HTTP/" in response:
                item['ping'] = int((time.time() - start_time) * 1000)
                return item
        return None
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
            # Разделяем на саму ссылку и название
            parts = code.split('#', 1)
            uri_part = parts[0]
            # Если названия нет, оставляем пустым
            original_name = parts[1] if len(parts) > 1 else ""
            
            parsed = urllib.parse.urlparse(uri_part)
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            port = int(parsed.netloc.split(':')[-1]) if ':' in parsed.netloc else 443
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [host])[0].lower()
            
            # Фильтруем по доменам (название здесь не участвует)
            if any(domain in f"{sni} {host}".lower() for domain in WHITE_LIST):
                ip = socket.gethostbyname(host)
                if ip not in seen_ips:
                    seen_ips.add(ip)
                    pre_filtered.append({
                        "uri": uri_part, 
                        "name": original_name,
                        "ip": ip, 
                        "port": port, 
                        "sni": sni
                    })
        except: continue

    processed_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(real_get_check, pre_filtered))
        processed_data = [r for r in results if r is not None]

    if not processed_data: return

    # Сортировка по пингу
    processed_data.sort(key=lambda x: x['ping'])
    
    final_output = []
    for i, item in enumerate(processed_data, 1):
        # Собираем обратно: ссылка#СтароеИмя — #Номер
        # Если старого имени нет, будет просто ссылка# — #Номер
        separator = " — " if item['name'] else ""
        final_output.append(f"{item['uri']}#{item['name']}{separator}#{i}")
    
    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_output))

if __name__ == "__main__":
    main()
