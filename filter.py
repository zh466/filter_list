import requests
import socket
import ssl
import urllib.parse
import concurrent.futures
import time

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
# Твой расширенный список доменов
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
            # Формируем запрос, максимально похожий на тест в приложении
            http_request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {item['sni']}\r\n"
                f"User-Agent: Mozilla/5.0\r\n"
                f"Connection: close\r\n\r\n"
            )
            ssock.sendall(http_request.encode())
            response = ssock.recv(1024)
            # Если получили любой HTTP ответ, значит прокси тянет трафик
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
            # Сохраняем строку в первозданном виде
            full_original_line = code
            
            # Для тестов и фильтрации вычленяем технические параметры
            uri_part = code.split('#')[0]
            parsed = urllib.parse.urlparse(uri_part)
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            port = int(parsed.netloc.split(':')[-1]) if ':' in parsed.netloc else 443
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [host])[0].lower()
            
            # Проверка по доменам
            if any(domain in f"{sni} {host}".lower() for domain in WHITE_LIST):
                ip = socket.gethostbyname(host)
                if ip not in seen_ips:
                    seen_ips.add(ip)
                    pre_filtered.append({
                        "original": full_original_line, # Сохраняем оригинал
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

    # Сортируем по пингу (лучшие сверху)
    processed_data.sort(key=lambda x: x['ping'])
    
    # Записываем в файл только оригинальные строки, без добавок
    final_output = [item['original'] for item in processed_data]
    
    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_output))

if __name__ == "__main__":
    main()
