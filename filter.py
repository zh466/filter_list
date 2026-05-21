import requests
import socket
import urllib.parse

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
# Твой полный список доменов
WHITE_LIST = [
    "api-maps.yandex.ru", "cdp.perekrestok.ru", "max.ru", "ozon.ru", 
    "vk.ru", "5post-gate.x5.ru", "ads.x5.ru", "eh.vk.com", 
    "sso.passport.yandex.ru", "m.ok.ru", "kinopoisk.ru",
    "cloud.mail.ru", "a.wb.ru",
    "dzen.ru", "mail.ru", "ya.ru", "www.avito.ru", "vkvideo.ru", "yandex.ru", "smartcaptcha.yandexcloud.net", "cluster-russia-3.firstvideocdn.ru", "x5.ru", "cdp.x5.ru"
]

def main():
    try:
        response = requests.get(SOURCE_URL, timeout=15)
        raw_codes = response.text.splitlines()
    except: 
        return
    
    valid_configs = []
    seen_ips = set() 

    for code in raw_codes:
        code = code.strip()
        if not code.startswith("vless://"): 
            continue
            
        try:
            # Вычленяем хост для проверки по белому списку
            uri_part = code.split('#')[0]
            parsed = urllib.parse.urlparse(uri_part)
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [host])[0].lower()
            
            # Если домен совпадает с белым списком
            if any(domain in f"{sni} {host}".lower() for domain in WHITE_LIST):
                try:
                    # Убираем дубли по IP, чтобы список был компактным
                    ip = socket.gethostbyname(host)
                    if ip not in seen_ips:
                        seen_ips.add(ip)
                        valid_configs.append(code) # Сохраняем строку целиком (оригинал)
                except:
                    continue
        except: 
            continue

    if not valid_configs: 
        return
    
    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_configs))

if __name__ == "__main__":
    main()
