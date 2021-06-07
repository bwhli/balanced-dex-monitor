from datetime import datetime
import pytz
import requests


def contract_to_name(contract):
    if contract == "cx2609b924e33ef00b648a409245c7ea394c467824":
        return "sICX"
    elif contract == "cxf61cd5a45dc9f91c15aa65831a30a90d59a09619":
        return "BALN"
    elif contract == "cx88fd7df7ddff82f7cc735c871dc519838cb235bb":
        return "bnUSD"
    else:
        return contract


def hex_to_int(n, exa: int = 18, dec: int = 2):
    result = n / 10 ** exa
    if (result).is_integer():
        return f"{int(result):,.0f}"
    else:
        return f"{result:,.4f}"


def format(s):
    if s[:2] == "0x":
        return int(s, 16)
    if s[:2] == "cx":
        return contract_to_name(s)
    else:
        return s


def send_discord_notification(url, embeds):
    payload = {
        "username": "RHIZOME Swap Monitor",
        "embeds": [embeds],
    }
    r = requests.post(url, json=payload)
    print(r.text)
