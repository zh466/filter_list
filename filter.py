import requests
import socket

SOURCE_URL = "https://github.com/zieng2/wl/blob/main/vless_lite.txt"
BLOCKLIST_URL = "https://antifilter.network/download/ip_sum.txt"

def get_ip(address):
    try:
        return socket.gethostbyname(address)
    except:
        return None

def main():
    blocked_data = requests.get(BLOCKLIST_URL).text
    my_codes = requests.get(SOURCE_URL).text.splitlines()
    
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
