import requests



def contract_to_name(contract):
    if contract == "cx2609b924e33ef00b648a409245c7ea394c467824":
        return "sICX"
    elif contract == "cxf61cd5a45dc9f91c15aa65831a30a90d59a09619":
        return "BALN"
    elif contract == "cx88fd7df7ddff82f7cc735c871dc519838cb235bb":
        return "bnUSD"


def hex_to_int(hex, exa: int = 0, fmt = None):
    if exa > 0:
        result =  int(hex, 16) / 10 ** exa
    else:
        result = int(hex, 16)
    if not fmt: 
        return result


def send_discord_notification(url, content):
    payload = {
        "username": "RHIZOME Swap Monitor",
        "avatar_url": "",
        "content": content,
    }
    requests.post(url, data=payload)
