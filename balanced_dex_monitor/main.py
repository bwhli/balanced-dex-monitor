from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.exception import JSONRPCException
from process import process_events
from rq import Queue
from time import sleep
from worker import conn

ICON_SERVICE = IconService(HTTPProvider("https://ctz.solidwallet.io", 3))

q = Queue(connection=conn)

# Initialize latest block.
block = ICON_SERVICE.get_block("latest")["height"]

while True:
    while True:
        try:
            ICON_SERVICE.get_block(block)
        except JSONRPCException:
            sleep(2)
            continue
        else:
            print(f"Checking block {block} for swaps...")
            q.enqueue(process_events, block)
            sleep(2)
            block += 1
