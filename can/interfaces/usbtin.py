"""
Interface for the USBtin module

Implementation references:
* Uses the pyUSBTin API (https://github.com/fishpepper/pyUSBtin)
* Interfaces with the USBtin module (https://www.fischl.de/usbtin/)
"""

from typing import List, Optional, Tuple, Any

import logging
import pyusbtin  # type: ignore
import can

logger = logging.getLogger(__name__)


class USBtinBus(can.BusABC):
    """
    usbtin interface
    """

    def __init__(self, channel: str, baudrate: int):
        super().__init__(channel, baudrate=baudrate)

        self.usbtin = pyusbtin.usbtin.USBtin()
        self.baudrate = baudrate
        self.usbtin.connect(channel)
        self.rx_fifo: List[Any] = []
        self.channel_info = "usbtin"

        self.usbtin.open_can_channel(self.baudrate, pyusbtin.usbtin.USBtin.ACTIVE)
        self.usbtin.add_message_listener(self._bridge_cb)

    def _bridge_cb(self, msg: Any) -> None:
        self.rx_fifo.append(msg)

    def _recv_internal(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[can.Message], bool]:
        if len(self.rx_fifo) == 0:
            return None, False

        canmsg = self.rx_fifo.pop(0)
        data = [
            canmsg[0],
            canmsg[1],
            canmsg[2],
            canmsg[3],
            canmsg[4],
            canmsg[5],
            canmsg[6],
            canmsg[7],
        ]
        msg = can.Message(
            arbitration_id=canmsg.mid,
            dlc=canmsg.dlc,
            data=data[: canmsg.dlc],
            is_remote_frame=canmsg.rtr,
        )

        return msg, False

    def send(self, msg: can.Message, timeout: Optional[float] = None) -> None:
        data = list(msg.data)
        pymsg = pyusbtin.canmessage.CANMessage(
            mid=msg.arbitration_id, dlc=msg.dlc, data=data
        )
        self.usbtin.send(pymsg)

    def shutdown(self) -> None:
        self.usbtin.close_can_channel()
        self.usbtin.disconnect()

    @staticmethod
    def _detect_available_configs() -> List[can.typechecking.AutoDetectedConfig]:
        raise NotImplementedError()
