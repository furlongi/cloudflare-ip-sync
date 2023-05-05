# Cloudflare IP Sync

Small script to keep your ip up to date in cloudflare if you have a dynamic ip.

Needs a config.json file:
```
{
    "api_token": "", # cloudflare api token
    "zone_ids": [
        "", # Zone ids. Found on url
    ]
}
```

Also needs a storage.json file. This is for easy ip comparison without pinging cloudlfare too often. Can be kept empty string on init.
```
{"current_ip": ""}
```

## Process:
1. Fetch local config and storage jsons
2. Ping external site for your external ip

If current ip is the same, do nothing. Else:

3. Verify cloudlfare api is valid.
4. Fetch records associated to the zone
5. For each record of type A (you can change this), update the ip
6. Store new external ip locally
