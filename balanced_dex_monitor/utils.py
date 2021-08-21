import os
import requests
from dotenv import load_dotenv

load_dotenv()


def contract_to_ticker(contract):
    if contract == "cx2609b924e33ef00b648a409245c7ea394c467824":
        return "sICX"
    elif contract == "cxf61cd5a45dc9f91c15aa65831a30a90d59a09619":
        return "BALN"
    elif contract == "cx88fd7df7ddff82f7cc735c871dc519838cb235bb":
        return "bnUSD"
    elif contract is None:
        return "ICX"


def format_number(num, exa=18):
    result = num / 10 ** exa
    if result.is_integer():
        return f"{result:,.0f}"
    else:
        return f"{result:,.4f}"


def hex_to_int(hex):
    return int(hex, 16)


def send_discord_notification(message):
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    payload = {
        "username": "Balanced DEX Monitor",
        "content": message,
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)
