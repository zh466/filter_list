import requests
import socket
import urllib.parse

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
BLOCKLIST_URL = "https://antifilter.download/list/ip.txt"

def get_ip(address):
    try:
        return socket.gethostbyname(address)
    except:
        return None

def main():
    try:
        blocked_data = requests.get(BLOCKLIST_URL, timeout=15).text
        my_codes = requests.get(SOURCE_URL, timeout=15).text.splitlines()
    except:
        return
    
    valid_codes = []
    
    for code in my_codes:
        if not code.startswith("vless://"): continue
        
        try:
            parsed = urllib.parse.urlparse(code)
            params = urllib.parse.parse_qs(parsed.query)
            
            # 1. Проверяем SNI (если он есть)
            sni = params.get('sni', [None])[0]
            
            # 2. Проверяем сам адрес сервера (host)
            host = parsed.netloc.split('@')[-1].split(':')[0]
            
            # Проверка: если SNI или хост заканчиваются на .ru
            is_russian_domain = False
            if sni and sni.lower().endswith('.ru'):
                is_russian_domain = True
            elif host.lower().endswith('.ru'):
                is_russian_domain = True
                
            if not is_russian_domain:
                continue

            # 3. Дополнительная проверка IP, чтобы сервер не был в бане
            ip = get_ip(host)
            if ip and ip not in blocked_data:
                valid_codes.append(code)
        except:
            continue
    
    with open("valid_vless.txt", "w") as f:
        f.write("\n".join(valid_codes))

if __name__ == "__main__":
    main()
