import pytz
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from balanced_dex_monitor.utils import (
    format,
    hex_to_int,
    send_discord_notification
)

# Geometry endpoint.
API_ENDPOINT = "http://icon.geometry-dev.net/api/v1"

# ICON stuff.
BALANCED_DEX_ADDRESS = "cxa0af3165c08318e988cb30993b3048335b94af6c"
ICON_SERVICE = IconService(HTTPProvider("https://ctz.solidwallet.io", 3))

# Discord stuff.
RHIZOME_INFRA_ALERTS_WH = "https://discord.com/api/webhooks/850953309433888772/i5LMnm2hWAO2Z8hsNSUCr2ILHoumCdhvJ95W1CbUzCkVsmPmtfte5sK-7hlMwjcjxtbV"
SWAP_NOTIFICATIONS_WH = "https://discord.com/api/webhooks/851316049780670535/F8pcC3oGi-RkfjGl2JAB1E2-kjbayPbk_myz8qyhu8zV8-_AVeKU2Xzt7T0knZ--f0VG"  # noqa 503

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
    block_height, tx_hash, data, indexed = (
        event["block_number"],
        event["transaction_hash"],
        event["data"],
        event["indexed"],
    )
    if (  # Check if event is a Balaced DEX swap.
        indexed[0]
        == "Swap(int,Address,Address,Address,Address,Address,int,int,int,int,int,int,int,int,int)"  # noqa 503
    ):
        print("This is a swap. Processing swap now...")
        process_swap_event(block_height, tx_hash, data, indexed)


def process_swap_event(block_height, tx_hash, data, indexed):
    _, pool_id, base_token = [format(indexed[i])
                              for i in range(0, len(indexed))]
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
    ) = [format(data[i]) for i in range(0, len(data))]

    # Format variables that need to be divided by 10 ** 18.
    from_value = hex_to_int(from_value, 18, 2)
    to_value = hex_to_int(to_value, 18, 2)
    lp_fees = hex_to_int(lp_fees, 18, 2)
    baln_fees = hex_to_int(baln_fees, 18, 2)
    pool_base = hex_to_int(pool_base, 18, 2)
    pool_quote = hex_to_int(pool_quote, 18, 2)
    ending_price = hex_to_int(ending_price, 18, 2)
    fill_price = hex_to_int(fill_price, 18, 2)

    print((
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
    ))

    # Set Discord color and order details based on order type.
    if base_token == to_token:  # Buy order.
        color = 3066993  # Green
        order_details = f"Bought: {to_value} {to_token}\n"\
                        f"With: {from_value} {from_token}\n"\
                        f"Fill Price: {ending_price} {from_token}\n"\
                        f"Fees: {lp_fees} {from_token}"
    elif base_token == base_token:  # Sell order.
        color = 15158332  # Red
        order_details = f"Sold: {from_value} {base_token}\n"\
                        f"For: {to_value} {to_token}\n"\
                        f"Fill Price: {ending_price} {to_token}\n"\
                        f"Fees: {lp_fees} {from_token}"

    # Set pool details.
    pool_map = {
        1: ("sICX", "ICX"),
        2: ("sICX", "bnUSD"),
        3: ("BALN", "bnUSD"),
        4: ("BALN", "sICX")
    }

    pool = (
        f"Base: {pool_base} {pool_map[pool_id][0]}\n"  # noqa 503
        f"Quote: {pool_quote} {pool_map[pool_id][1]}"  # noqa 503
    )

    print(pool)

    # Set metadata details.
    metadata = (
        f"Address: [{sender}](https://tracker.icon.foundation/address/{sender})\n"
        f"Hash: [{tx_hash[:32]}...](https://tracker.icon.foundation/transaction/{tx_hash})\n"
        f"Timestamp: {datetime.fromtimestamp(timestamp / 1000000, tz=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S UTC')}"  # noqa 503
    )

    print(metadata)

    embeds = {
        "title": f"New Swap at Block #{block_height:,}",
        "url": f"https://tracker.icon.foundation/transaction/{tx_hash}",
        "color": color,
        "footer": {
            "text": "Brought to you by RHIZOME."
        },
        "fields": [
            {
                "name": "🔁 **Swap Details**",
                "value": order_details
            },
            {
                "name": f"💦 **{pool_map[pool_id][0]}/{pool_map[pool_id][1]} Pool Details**",  # noqa 503
                "value": pool
            },
            {
                "name": "📝 **Metadata**",
                "value": metadata
            }
        ]
    }

    print(embeds)

    send_discord_notification(SWAP_NOTIFICATIONS_WH, embeds)


def main():
    block = ICON_SERVICE.get_block("latest")["height"]

    if DEBUG_MODE:
        block = 35285328  # BALN/sICX, sICX to BALN (buy order)
        block = 35345275  # BALN/sICX, BALN to sICX (sell order)
        block = 35346792  # bnusd / sICX

    while True:

        print(f"Checking block {block} for Balanced events...")

        # Get contract events related to Balanced DEX.
        balanced_dex_events = get_balanced_dex_events(block)

        if len(balanced_dex_events) > 0:
            print(f"There are {len(balanced_dex_events)} Balanced event(s) in block {block}")  # noqa 503
            with ThreadPoolExecutor() as executor:
                executor.map(process_event, balanced_dex_events)
        else:
            print(f"There are no Balanced event(s) in block {block}...")

        if DEBUG_MODE:
            break

        block += 1


if __name__ == "__main__":
    main()
