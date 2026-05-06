import requests
import socket
import urllib.parse
import time

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"
BLOCKLIST_URL = "https://antifilter.download/list/ip.txt"

def get_flag(country_code):
    if not country_code or len(country_code) != 2 or country_code == "IP":
        return "🌐"
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())

def get_info(address):
    try:
        ip = socket.gethostbyname(address)
        # Используем альтернативное API (ipwho.is) - оно быстрее и стабильнее
        res = requests.get(f"https://ipwho.is/{ip}", timeout=5).json()
        if res.get("success"):
            return ip, res.get("country_code")
        return ip, "IP"
    except:
        return None, "IP"

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
            
            # Фильтр только по .ru
            if not (sni.endswith('.ru') or host.endswith('.ru')):
                continue

            ip, country_code = get_info(host)
            time.sleep(0.3) 
            
            if ip and ip not in blocked_data:
                flag = get_flag(country_code)
                display_sni = sni if sni else host
                # Формат как в твоем примере: Флаг Название — #Номер
                new_name = f"{flag} {display_sni} — #{counter}"
                
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
