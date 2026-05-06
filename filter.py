import requests
import socket
import urllib.parse

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
WHITE_LIST_URL = "https://raw.githubusercontent.com/hxehex/russia-mobile-internet-whitelist/issues/56"
BLOCKLIST_URL = "https://antifilter.download/list/ip.txt"

def get_ip(address):
    try:
        return socket.gethostbyname(address)
    except:
        return None

def main():
    try:
        blocked_data = requests.get(BLOCKLIST_URL, timeout=15).text
        white_list = set(requests.get(WHITE_LIST_URL, timeout=15).text.splitlines())
        my_codes = requests.get(SOURCE_URL, timeout=15).text.splitlines()
    except:
        return
    
    valid_codes = []
    
    for code in my_codes:
        if not code.startswith("vless://"): continue
        
        try:
            parsed = urllib.parse.urlparse(code)
            params = urllib.parse.parse_qs(parsed.query)
            
            # Извлекаем SNI из кода
            sni = params.get('sni', [None])[0]
            
            # Если SNI нет или его нет в белом списке — пропускаем
            if not sni or sni not in white_list:
                continue

            # Проверяем IP сервера на общую блокировку
            host = parsed.netloc.split('@')[-1].split(':')[0]
            ip = get_ip(host)
            
            if ip and ip not in blocked_data:
                valid_codes.append(code)
        except:
            continue
    
    with open("valid_vless.txt", "w") as f:
        f.write("\n".join(valid_codes))

if __name__ == "__main__":
    main()
