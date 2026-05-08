import requests

def get_flag(country_code):
    if not country_code or len(country_code) != 2: return "🌐"
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())

def main():
    try:
        with open("step1_filtered.txt", "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except: return

    items = []
    for line in lines:
        link, ip, ping = line.split('|')
        items.append({"link": link, "ip": ip, "ping": int(ping)})

    # Пакетный запрос данных о странах
    ips = [item["ip"] for item in items]
    ip_info = {}
    for i in range(0, len(ips), 100):
        batch = ips[i:i+100]
        try:
            res = requests.post("http://ip-api.com/batch?fields=query,country,countryCode", json=batch).json()
            for info in res:
                ip_info[info["query"]] = {
                    "name": info.get("country", "Unknown"),
                    "code": info.get("countryCode", "ZZ")
                }
        except: pass

    # Сортировка по странам и пингу
    items.sort(key=lambda x: (ip_info.get(x['ip'], {}).get('code') == 'RU', x['ping']))

    final_list = []
    for i, item in enumerate(items, 1):
        info = ip_info.get(item['ip'], {"name": "Unknown", "code": "ZZ"})
        flag = get_flag(info['code'])
        # Формат: 🇧🇬Bulgaria-№1
        new_name = f"{flag}{info['name']}-№{i}"
        final_list.append(f"{item['link']}#{new_name}")

    with open("valid_vless.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_list))

if __name__ == "__main__":
    main()
