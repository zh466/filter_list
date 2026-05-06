import requests
import socket

SOURCE_URL = "ТВОЯ_ССЫЛКА_НА_RAW_СПИСОК_VLESS"
BLOCKLIST_URL = "https://antifilter.download/list/ip.txt"

def get_ip(address):
    try:
        return socket.gethostbyname(address)
    except:
        return None

def main():
    try:
        r = requests.get(BLOCKLIST_URL, timeout=15)
        blocked_data = r.text
    except:
        return

    try:
        my_codes = requests.get(SOURCE_URL, timeout=15).text.splitlines()
    except:
        return
    
    valid_codes = []
    
    for code in my_codes:
        if not code.startswith("vless://"): continue
        
        try:
            host = code.split('@')[1].split(':')[0]
            ip = get_ip(host)
            
            if ip and ip not in blocked_data:
                valid_codes.append(code)
        except:
            continue
    
    with open("valid_vless.txt", "w") as f:
        f.write("\n".join(valid_codes))

if name == "main":
    main()
