import requests
import threading
from datetime import datetime, timezone
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from time import sleep
from utils import contract_to_ticker, format_number, hex_to_int, send_discord_notification


ICON_SERVICE = IconService(HTTPProvider("https://ctz.solidwallet.io", 3))


def process_events(block):

    MAX_RETRY = 3

    def process_swaps(block):
        SWAP_API_ENDPOINT = "https://balanced.geometry.io/api/v1/dex/logs/Swap"

        i = 1
        while i < MAX_RETRY:
            try:
                url = f"{SWAP_API_ENDPOINT}?limit=1000&skip=0&min_block_number={block}&max_block_number={block}"
                r = requests.get(url)
                swaps = r.json()
                if len(swaps) > 0:
                    print(f"Processing {len(swaps)} swaps in Block {block}...")
                    for swap in swaps:
                        # block_height = swap["block_number"]
                        transaction_hash = swap["transaction_hash"]
                        # indexed = swap["indexed"]
                        data = swap["data"]

                        # pool_id = indexed[1]
                        # base_token = contract_to_ticker(indexed[2])
                        from_token = contract_to_ticker(data[0])
                        to_token = contract_to_ticker(data[1])
                        sender = data[2]
                        # receiver = data[3]
                        from_value = hex_to_int(data[4])
                        to_value = hex_to_int(data[5])
                        timestamp = datetime.fromtimestamp(hex_to_int(data[6]) / 1000000, tz=timezone.utc).replace(microsecond=0, tzinfo=None).isoformat()  # noqa 503
                        # lp_fees = hex_to_int(data[7])
                        # baln_fees = hex_to_int(data[8])
                        # pool_base = hex_to_int(data[9])
                        # pool_quote = hex_to_int(data[10])
                        # ending_price = hex_to_int(data[11])
                        # fill_price = hex_to_int(data[12])

                        message = f"`{timestamp} // {sender}` **>> [{format_number(from_value)} {from_token} for {format_number(to_value)} {to_token}](https://tracker.icon.foundation/transaction/{transaction_hash})**"  # noqa 503

                        send_discord_notification(message)

                    break
                else:
                    print("Sleeping for 1 second...")
                    sleep(1)
                    i += 1
            except Exception as e:
                print(e)

    def process_transfers(block):
        TRANSFER_API_ENDPOINT = "https://balanced.geometry.io/api/v1/contract/cx43e2eec79eb76293c298f2b17aec06097be606e0/logs"  # noqa 503

        i = 1
        while i < MAX_RETRY:
            try:
                url = f"{TRANSFER_API_ENDPOINT}?method=TokenTransfer&min_block_number={block}&max_block_number={block}&limit=1000&skip=0"  # noqa 503
                r = requests.get(url)
                transfers = r.json()
                print(f"Processing {len(transfers)} transfers in Block {block}...")  # noqa 503
                if len(transfers) > 0:
                    for transfer in transfers:
                        indexed = transfer["indexed"]
                        timestamp = transfer["item_timestamp"][:-1]
                        sender = transfer["from_address"]

                        transaction_hash = transfer["transaction_hash"]
                        icx_amount = ICON_SERVICE.get_transaction(transaction_hash)["value"]  # noqa 503
                        sicx_amount = hex_to_int(indexed[2])

                        message = f"`{timestamp} // {sender}` **>> [{format_number(icx_amount)} ICX for {format_number(sicx_amount)} sICX](https://tracker.icon.foundation/transaction/{transaction_hash})**"  # noqa 503

                        send_discord_notification(message)
                    break
                else:
                    print("Sleeping for 1 second...")
                    sleep(1)
                    i += 1
            except Exception as e:
                print(e)

    t1 = threading.Thread(target=process_swaps, args=(block,))
    t2 = threading.Thread(target=process_transfers, args=(block,))

    t1.start()
    t2.start()

    t1.join()
    t2.join()
