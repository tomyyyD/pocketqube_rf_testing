import tasko
from lib.pycubed import cubesat
from lib.radio_utils import transmission_queue as tq
from lib.radio_utils.disk_buffered_message import DiskBufferedMessage
from lib.radio_utils.image_buffered_message import ImageBufferedMessage


async def send_messages():
    tq.push(ImageBufferedMessage("/sd/images/packeted_iamge_test.jpeg", 237))
    while not tq.empty():
        msg = tq.peek()
        while not msg.done():
            pkt, with_ack = msg.packet()
            print(pkt)
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
