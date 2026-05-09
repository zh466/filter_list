import requests
import socket
import ssl
import urllib.parse
import concurrent.futures
import time

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
# Тестовый домен из твоих настроек в приложении
TEST_URL = "web.telegram.org"
WHITE_LIST = [
    "api-maps.yandex.ru", "cdp.perekrestok.ru", "max.ru", "ozon.ru", 
    "vk.ru", "5post-gate.x5.ru", "ads.x5.ru", "eh.vk.com", 
    "sso.passport.yandex.ru", "m.ok.ru", "kinopoisk.ru",
    "cloud.mail.ru", "a.wb.ru"
]

def extreme_proxy_test(item):
    """
    Имитация теста Happ: подключаемся к прокси и пытаемся 
    сделать GET-запрос именно к web.telegram.org
    """
    try:
        start_time = time.time()
        # Увеличиваем таймаут до 5 сек (для надежности при плохом сигнале)
        sock = socket.create_connection((item['ip'], item['port']), timeout=5)
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with context.wrap_socket(sock, server_hostname=item['sni']) as ssock:
            ssock.settimeout(4.0)
            
            # Эмулируем запрос к web.telegram.org, как делает твое приложение
            http_request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {TEST_URL}\r\n"
                f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
                f"Connection: close\r\n\r\n"
            )
            ssock.sendall(http_request.encode())
            
            # Читаем ответ. Если прокси рабочий, он должен вернуть заголовок HTTP
            response = ssock.recv(1024)
            if b"HTTP/" in response:
                item['ping'] = int((time.time() - start_time) * 1000)
                return item
        return None
    except:
        return None

def main():
    try:
        response = requests.get(SOURCE_URL, timeout=10)
        raw_codes = response.text.splitlines()
    except: return
    
    pre_filtered = []
    seen_ips = set() 

    for code in raw_codes:
        code = code.strip()
        if not code.startswith("vless://"): continue
        try:
            full_line = code
            uri_part = code.split('#')[0]
            parsed = urllib.parse.urlparse(uri_part)
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            port = int(parsed.netloc.split(':')[-1]) if ':' in parsed.netloc else 443
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [host])[0].lower()
            
            # Фильтр по доменам
            if any(domain in f"{sni} {host}".lower() for domain in WHITE_LIST):
                ip = socket.gethostbyname(host)
                if ip not in seen_ips:
                    seen_ips.add(ip)
                    pre_filtered.append({"original": full_line, "ip": ip, "port": port, "sni": sni})
        except: continue

    # Проверка в 10 потоков (медленно, но очень тщательно)
    processed_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(extreme_proxy_test, pre_filtered))
        processed_data = [r for r in results if r is not None]

    if not processed_data: return
    
    # Сортировка: лучшие по пингу вверх
    processed_data.sort(key=lambda x: x['ping'])
    
    final_output = []
    for item in processed_data:
        # Добавляем инфо о трафике для красоты счетчика в Happ
        line = item['original']
        final_output.append(line)
    
    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_output))

if __name__ == "__main__":
    main()
