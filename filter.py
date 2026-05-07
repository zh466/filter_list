import requests
import urllib.parse

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"

def main():
    try:
        response = requests.get(SOURCE_URL, timeout=15)
        if response.status_code != 200:
            return
        raw_codes = response.text.splitlines()
    except:
        return
    
    valid_codes = []
    seen_links = set() 

    for code in raw_codes:
        code = code.strip()
        if not code.startswith("vless://"):
            continue
            
        try:
            # 1. Отделяем техническую часть от старого названия
            clean_link = code.split('#')[0]
            
            # 2. Парсим параметры, чтобы вытащить SNI или Host
            parsed = urllib.parse.urlparse(clean_link)
            params = urllib.parse.parse_qs(parsed.query)
            
            # Достаем SNI, если его нет — берем Host (адрес сервера)
            sni = params.get('sni', [''])[0].lower()
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            display_name = sni if sni else host

            # 3. Фильтруем: оставляем только если в названии есть .ru
            if ".ru" in display_name:
                if clean_link not in seen_links:
                    # 4. Собираем ссылку заново с НОВЫМ названием
                    # Кодируем название, чтобы не было ошибок в приложении
                    safe_name = urllib.parse.quote(display_name)
                    valid_codes.append(f"{clean_link}#{safe_name}")
                    seen_links.add(clean_link)
        except:
            continue
    
    # Записываем результат
    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_codes))

if __name__ == "__main__":
    main()

