import requests
import socket
import urllib.parse

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
# Твой максимально полный список доменов
WHITE_LIST = [
    "api-maps.yandex.ru", "cdp.perekrestok.ru", "max.ru", "ozon.ru", 
    "vk.ru", "5post-gate.x5.ru", "ads.x5.ru", "eh.vk.com", 
    "sso.passport.yandex.ru", "m.ok.ru", "kinopoisk.ru",
    "cloud.mail.ru", "a.wb.ru",
    "dzen.ru", "mail.ru", "ya.ru", "www.avito.ru", "vkvideo.ru", "yandex.ru", "cluster-russia-1.firstvideocdn.ru"
]

def main():
    try:
        # Загружаем список
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
            # Для фильтрации нам нужно вытащить адрес или SNI
            uri_part = code.split('#')[0]
            parsed = urllib.parse.urlparse(uri_part)
            
            # Извлекаем хост и параметры
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [host])[0].lower()
            
            # Проверяем, есть ли хоть один домен из белого списка в хосте или SNI
            # Мы используем поиск подстроки, чтобы ya.ru ловил и sso.ya.ru
            if any(domain in f"{sni} {host}".lower() for domain in WHITE_LIST):
                # Проверка на дубликаты по IP (чтобы не забивать Happ одинаковыми серверами)
                try:
                    ip = socket.gethostbyname(host)
                    if ip not in seen_ips:
                        seen_ips.add(ip)
                        valid_configs.append(code) # Сохраняем оригинал целиком
                except:
                    # Если IP не резолвится, сервер точно не рабочий, пропускаем
                    continue
        except: 
            continue

    if not valid_configs: 
        return
    
    # Записываем результат
    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_configs))

if __name__ == "__main__":
    main()
