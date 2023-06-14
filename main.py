import tasko
from lib.pycubed import cubesat
from lib.radio_utils import transmission_queue as tq
from lib.radio_utils.disk_buffered_message import DiskBufferedMessage


async def send_messages():
    tq.push(DiskBufferedMessage("/sd/images/image_7.jpeg"))
    while not tq.empty():
        msg = tq.peek()
        while not msg.done():
            pkt, with_ack = msg.packet()
            if with_ack:
                if await cubesat.radio.send_with_ack(pkt):
                    msg.ack()
                else:
                    msg.no_ack()
            else:
                await cubesat.radio.send(pkt, keep_listening=True)

        if tq.peek().done():
            tq.pop()

tasko.add_task(send_messages(), 1)
tasko.run()
