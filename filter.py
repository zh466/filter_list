import requests
import socket
import urllib.parse

SOURCE_URL = "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt"

def get_flag(country_code):
    if not country_code or len(country_code) != 2 or country_code == "ZZ":
        return "🌐"
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())

def main():
    try:
        response = requests.get(SOURCE_URL, timeout=15)
        raw_codes = response.text.splitlines()
    except: return
    
    processed_data = []
    seen_ips = set() # ЖЕСТКИЙ ФИЛЬТР: один IP — один сервер в списке

    for code in raw_codes:
        code = code.strip()
        if not code.startswith("vless://"): continue
            
        try:
            clean_link = code.split('#')[0]
            parsed = urllib.parse.urlparse(clean_link)
            params = urllib.parse.parse_qs(parsed.query)
            
            sni = params.get('sni', [''])[0].lower()
            host = parsed.netloc.split('@')[-1].split(':')[0].lower()
            display_name = sni if sni else host

            if ".ru" in display_name:
                try:
                    ip = socket.gethostbyname(host)
                    # Если этот IP уже есть в списке — пропускаем. Это уберет сотни дублей.
                    if ip in seen_ips: continue
                    
                    seen_ips.add(ip)
                    processed_data.append({
                        "link": clean_link,
                        "name": display_name,
                        "ip": ip
                    })
                except: continue
        except: continue

    if not processed_data: return

    # Пакетная проверка через ip-api (самый точный для VPN/Hosting IP)
    ip_country_map = {}
    ips_to_check = [item["ip"] for item in processed_data]
    
    for i in range(0, len(ips_to_check), 100):
        batch = ips_to_check[i:i+100]
        try:
            # Запрашиваем страну + имя провайдера (для доп. проверки)
            res = requests.post("http://ip-api.com/batch?fields=query,countryCode,isp", json=batch, timeout=10).json()
            for item in res:
                query = item.get("query")
                country = item.get("countryCode", "ZZ")
                isp = item.get("isp", "").lower()
                
                # 100% ТОЧНОСТЬ: Если провайдер российский (yandex, vdsina, ihor и т.д.), 
                # но база врет про Сейшелы — ставим RU.
                rus_isps = ['yandex', 'vdsina', 'ihor', 'selectel', 'mtt', 'beeline', 'mts', 'megafon', 'rostelecom']
                if any(x in isp for x in rus_isps):
                    country = "RU"
                
                ip_country_map[query] = country
        except: pass

    # Сортировка: Сначала заграница, потом РФ
    processed_data.sort(key=lambda x: (ip_country_map.get(x['ip'], 'ZZ') == 'RU', x['name']))
    
    valid_codes = []
    for i, item in enumerate(processed_data, 1):
        country_code = ip_country_map.get(item["ip"], "ZZ")
        flag = get_flag(country_code)
        
        new_name = f"{flag} {item['name']} — #{i}"
        safe_name = urllib.parse.quote(new_name)
        valid_codes.append(f"{item['link']}#{safe_name}")
    
    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_codes))

if __name__ == "__main__":
    main()

