import requests
import socket
import urllib.parse
import time

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
BLOCKLIST_URL = "https://antifilter.download/list/ip.txt"

def get_info(address):
    try:
        ip = socket.gethostbyname(address)
        # Получаем двухбуквенный код (RU, NL, DE)
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode", timeout=5).json()
        if res.get("status") == "success":
            return ip, res.get("countryCode")
        return ip, "UN"
    except:
        return None, "UN"

def main():
    try:
        blocked_data = requests.get(BLOCKLIST_URL, timeout=15).text
        my_codes = requests.get(SOURCE_URL, timeout=15).text.splitlines()
    except:
        return
    
    valid_codes = []
    counter = 1
    
    for code in my_codes:
        if not code.startswith("vless://"): continue
        
        try:
            parsed = urllib.parse.urlparse(code)
            params = urllib.parse.parse_qs(parsed.query)
            sni = params.get('sni', [''])[0].lower()
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            
            if not (sni.endswith('.ru') or host.endswith('.ru')):
                continue

            ip, country_code = get_info(host)
            time.sleep(0.4) # Небольшая пауза для стабильности API
            
            if ip and ip not in blocked_data:
                # Формат: КОД_СТРАНЫ SNI #НОМЕР
                # Именно такой формат (код страны в начале) заставляет Hiddify менять иконку
                new_name = f"{country_code.upper()} {sni if sni else host} #{counter}"
                
                base_part = code.split('#')[0]
                safe_name = urllib.parse.quote(new_name)
                valid_codes.append(f"{base_part}#{safe_name}")
                counter += 1
        except:
            continue
    
    with open("valid_vless.txt", "w") as f:
        f.write("\n".join(valid_codes))

if __name__ == "__main__":
    main()
