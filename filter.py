import requests
import socket

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
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

if __name__ == "__main__":
    main()
