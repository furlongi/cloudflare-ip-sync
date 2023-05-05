import json
import requests
from typing import Tuple, List, Dict, cast, Optional

class CloudFlareError(Exception):
    pass

class ExternalIPError(Exception):
    pass

def load_config() -> Tuple[str, List[str]]:
    '''
    {
        "api_token": "",
        "zone_ids": [
            "",
        ]
    }
    '''
    configs = None
    with open("./config.json", "r", encoding="utf-8") as file:
        configs = json.load(file)

    if configs is None:
        raise FileExistsError("Error when loading configs.json")

    if "api_token" not in configs:
        raise KeyError("api_token not in configs")
    
    if len(configs.get("zone_ids", [])) < 1:
        raise KeyError("zone_ids is either missing or empty")

    return configs["api_token"], configs["zone_ids"]

def load_current_ip() -> str:
    '''
    {
        "current_ip": ""
    }
    '''
    with open("./storage.json", "r", encoding="utf-8") as file:
        configs = json.load(file)
        return configs.get("current_ip", "")

def store_new_ip(new_ip: str):
    print(f"[STORE] Storing new ip {new_ip}")
    with open("./storage.json", "w") as file:
        file.write(json.dumps(
            {
                "current_ip": new_ip
            }
        ))

def get_external_ip() -> Optional[str]:
    url = "http://ip.42.pl/raw"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    return str(response.text)

def headers(token: str) -> Dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def verify_cloudflare(token: str):
    response = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", headers=headers(token))

    # print(response.content)
    is_valid = response.status_code == 200 and response.json().get("success", False)
    if not is_valid:
        raise CloudFlareError("Unable to verify token.")

def sync_ips(token: str, external_ip: str, zones: List[str]):
    for zone in zones:
        print(f"[ZONE] Fetching records for zone {zone}")
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/zones/{zone}/dns_records",
            headers=headers(token)
        )
        response = cast(dict, response.json())

        if not response.get("success", False):
            print(f"[ZONE] Unable to get list of dns records for zone {zone}")
            continue

        for record in response["result"]:
            if record["type"] not in ["A"]:
                continue

            if record["content"] != external_ip:
                # Update happens here
                print(f"[RECORD] Current IP: {external_ip}. Cloudflare IP: {record['content']}")

                payload = {
                    "content": external_ip,
                    "name": record["name"],
                    "type": record["type"],
                    "proxied": record["proxied"]
                }

                response = requests.put(
                    f"https://api.cloudflare.com/client/v4/zones/{zone}/dns_records/{record['id']}",
                    headers=headers(token),
                    data=json.dumps(payload)
                )

                if response.json().get("success", False):
                    print(f"[RECORD] Successfully updated zone {record['zone_name']}")
                else:
                    print(f"[RECORD] Failed to update {record['zone_name']}: {response.json()}")


def main():
    token, zones = load_config()
    current_ip = load_current_ip()
    external_ip = get_external_ip()

    if external_ip is None:
        raise ExternalIPError("[EXT IP] Error retrieving external IP")
    
    if current_ip != external_ip:
        verify_cloudflare(token)
        sync_ips(token, external_ip, zones)
        store_new_ip(external_ip)

if __name__ == "__main__":
    main()