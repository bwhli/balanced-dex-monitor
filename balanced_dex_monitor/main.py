import json
import requests
from concurrent.futures import ThreadPoolExecutor
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.exception import JSONRPCException
from balanced_dex_monitor.utils import contract_to_name, hex_to_int, send_discord_notification

# Geometry endpoint.
API_ENDPOINT = "http://icon.geometry-dev.net/api/v1"

# ICON stuff.
BALANCED_DEX_ADDRESS = "cxa0af3165c08318e988cb30993b3048335b94af6c"
ICON_SERVICE = IconService(HTTPProvider("https://ctz.solidwallet.io", 3))

# Discord stuff.
RHIZOME_INFRA_ALERTS_WH = "https://discord.com/api/webhooks/850953309433888772/i5LMnm2hWAO2Z8hsNSUCr2ILHoumCdhvJ95W1CbUzCkVsmPmtfte5sK-7hlMwjcjxtbV"
SWAP_NOTIFICATIONS_WH = "https://discord.com/api/webhooks/850689815959175198/HR_JiTpFVrEU_4PlrPBNmoFtM_9GPDlYUA7byQ11rHHeXadAcBs55frXUrHBf6szM3L1"  # noqa 503

DEBUG_MODE = False


def get_balanced_dex_events(block):
    url = f"{API_ENDPOINT}/events/block/{block}?skip=0&limit=0"
    # Get transaction data for latest block.
    while True:
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if r.status_code == 404:
                continue
            else:
                send_discord_notification(RHIZOME_INFRA_ALERTS_WH, err)
                continue
        else:
            event_logs = r.json()

            filtered_event_logs = [
                event_log
                for event_log in event_logs
                if event_log["address"] == BALANCED_DEX_ADDRESS
            ]

            return filtered_event_logs


def process_event(event):
    tx_hash, data, indexed = (
        event["transaction_hash"],
        event["data"],
        event["indexed"],
    )
    if (  # Check if event is a Balaced DEX swap.
        indexed[0]
        == "Swap(int,Address,Address,Address,Address,Address,int,int,int,int,int,int,int,int,int)"  # noqa 501
    ):
        process_swap_event(tx_hash, data, indexed)


def process_swap_event(tx_hash, data, indexed):
    print("Processing swap now...")
    _, token_id, base_token = [indexed[i] for i in range(0, len(indexed))]
    (
        from_token,
        to_token,
        sender,
        receiver,
        from_value,
        to_value,
        timestamp,
        lp_fees,
        baln_fees,
        pool_base,
        pool_quote,
        ending_price,
        fill_price,
    ) = [data[i] for i in range(0, len(data))]

    swap = {
        "token_id": hex_to_int(token_id),
        "base_token": contract_to_name(base_token),
        "from_token": contract_to_name(from_token),
        "to_token": contract_to_name(to_token),
        "sender": sender,
        "receiver": receiver,
        "from_value": hex_to_int(from_value, 18),
        "to_value": hex_to_int(to_value, 18),
        "timestamp": hex_to_int(timestamp),
        "lp_fees": hex_to_int(lp_fees, 18),
        "baln_fees": hex_to_int(baln_fees, 18),
        "pool_base": hex_to_int(pool_base, 18),
        "pool_quote": hex_to_int(pool_quote, 18),
        "ending_price": hex_to_int(ending_price, 18),
        "fill_price": hex_to_int(fill_price, 18),
    }

    content = f"""
    🔁 {sender} swapped **{swap['from_value']} {swap['from_token']}** for **{swap['to_value']} {swap['to_token']}** at an average price of {swap['fill_price']} {swap['from_token']}
[Click here to view the transaction](https://tracker.icon.foundation/transaction/{tx_hash}).
    """

    send_discord_notification(SWAP_NOTIFICATIONS_WH, content)


def main():
    latest_block = ICON_SERVICE.get_block("latest")["height"]

    if DEBUG_MODE:
        latest_block = 35285328

    while True:

        print(f"Checking block {latest_block} for swaps...")

        # Get contract events related to Balanced DEX.
        balanced_dex_events = get_balanced_dex_events(latest_block)

        if len(balanced_dex_events) > 0:
            print(f"There are {len(balanced_dex_events)} Balanced event(s) in block {latest_block}")
            with ThreadPoolExecutor() as executor:
                executor.map(process_event, balanced_dex_events)
        else:
            print(f"There are no Balanced event(s) in block {latest_block}...")

        if DEBUG_MODE:
            break

        latest_block += 1


if __name__ == "__main__":
    main()
