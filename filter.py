import requests
import socket
import ssl
import urllib.parse
import concurrent.futures
import time

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
WHITE_LIST = [
    "api-maps.yandex.ru", "cdp.perekrestok.ru", "max.ru", "ozon.ru", "vk.ru", 
    "5post-gate.x5.ru", "ads.x5.ru", "eh.vk.com", "sso.passport.yandex.ru", 
    "m.ok.ru", "kinopoisk.ru"
]

def extreme_ping_check(item):
    try:
        start_time = time.time()
        sock = socket.create_connection((item['ip'], item['port']), timeout=4)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_alpn_protocols(['h2', 'http/1.1'])
        with context.wrap_socket(sock, server_hostname=item['sni']) as ssock:
            ssock.settimeout(2.0)
            ssock.write(b'\x00')
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
            link_part = code.split('#')[0]
            parsed = urllib.parse.urlparse(link_part)
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            port = int(parsed.netloc.split(':')[-1]) if ':' in parsed.netloc else 443
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [host])[0].lower()
            
            if any(domain in f"{sni} {host}".lower() for domain in WHITE_LIST):
                ip = socket.gethostbyname(host)
                if ip not in seen_ips:
                    seen_ips.add(ip)
                    pre_filtered.append({"full_code": link_part, "ip": ip, "port": port, "sni": sni})
        except: continue

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(extreme_ping_check, pre_filtered))
        processed_data = [r for r in results if r is not None]

    if not processed_data: return

    # Сохраняем "сырой" результат для второго шага
    with open("step1_filtered.txt", "w", encoding="utf-8") as f:
        # Записываем ссылку и IP через разделитель, чтобы второму скрипту было проще
        for item in processed_data:
            f.write(f"{item['full_code']}|{item['ip']}|{item['ping']}\n")

if __name__ == "__main__":
    main()
