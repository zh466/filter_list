import requests
import socket
import urllib.parse
import geoip2.database
import os

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
BLOCKLIST_URL = "https://antifilter.download/list/ip.txt"
DB_PATH = 'country.mmdb'

def get_country(ip_address):
    try:
        with geoip2.database.Reader(DB_PATH) as reader:
            response = reader.country(ip_address)
            return response.country.iso_code or "ZZ"
    except:
        return "ZZ"

def main():
    if not os.path.exists(DB_PATH):
        print("GeoIP database not found!")
        return

    try:
        blocked_data = requests.get(BLOCKLIST_URL, timeout=15).text
        my_codes = requests.get(SOURCE_URL, timeout=15).text.splitlines()
    except:
        return
    
    temp_list = []
    for code in my_codes:
        if not code.startswith("vless://"): continue
        try:
            parsed = urllib.parse.urlparse(code)
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [''])[0].lower()
            
            # Фильтр по .ru
            if not (sni.endswith('.ru') or host.endswith('.ru')):
                continue

            ip = socket.gethostbyname(host)
            if ip in blocked_data: continue
            
            c_code = get_country(ip)
            
            temp_list.append({
                "code": code.split('#')[0],
                "sni": sni if sni else host,
                "country": c_code.upper()
            })
        except:
            continue
    
    # СОРТИРОВКА: (Сначала НЕ Россия, потом по алфавиту стран, Россия в конце)
    temp_list.sort(key=lambda x: (x['country'] == 'RU', x['country'], x['sni']))
    
    valid_codes = []
    for i, item in enumerate(temp_list, 1):
        # Название: код страны + SNI. Большинство приложений подхватят флаг по коду.
        new_name = f"{item['country']} {item['sni']} — #{i}"
        safe_name = urllib.parse.quote(new_name)
        valid_codes.append(f"{item['code']}#{safe_name}")
    
    with open("valid_vless.txt", "w") as f:
        f.write("\n".join(valid_codes))

if __name__ == "__main__":
    main()
