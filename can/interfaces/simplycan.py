import time
import logging
import sys
import simply_py as simply
from can import CanError, BusABC, Message

logger = logging.getLogger(__name__)

class SimplycanBus(BusABC):

    def __init__(self, channel, can_filters=None, bitrate=None, log_errors=True, **kwargs):
        """
        :param str channel:
            port of underlying serial or usb device (e.g. ``/dev/ttyUSB0``, ``COM8``, ...)
            Must not be empty.
        :param int bitrate:
            CAN Bitrate in bit/s. Value is stored in the adapter and will be used as default if no bitrate is specified
        """
        can_port = bytes(channel)
        if not simply.open(can_port):
            logger.info("Error opening CAN Channel")
            
        id = simply.identify()
        if not id: 
            logger.info("Error getting CAN Adapter details")

        res = simply.stop_can()
        res &= simply.initialize_can(bitrate/1000)
        res &= simply.start_can()
        if not res: 
            logger.info("Error initialising CAN Channel")

        self.channel_info = "IXXAT SimplyCAN USB-CAN" 
        logger.info("Using device: %s", self.channel_info)

        super(SimplycanBus, self).__init__(channel=channel,
                can_filters=can_filters, bitrate=bitrate,
                log_errors=log_errors, **kwargs)

    def _readmessage(self, timeout):

        # loop until we have read an appropriate message
        start = time.time()

        while True:

            # Log errors for now - low level driver does not throw exceptions on failed comms or disconnections
            try:
                res, msg = simply.receive()
            except Exception as e:
                logger.error("Exception on SimplycanBus._readmessage")
                raise 

            if res == 1:
                return msg

            # Check timeout if provided
            if timeout is not None:
                if (time.time() - start) > timeout:
                    return None
                    
    def _recv_internal(self, timeout):
        rx_msg = self._readmessage(timeout)

        if rx_msg is not None:
            msg = Message(
                arbitration_id=rx_msg.ident,
                is_extended_id=False,
                timestamp=time.time(),
                is_remote_frame=False,
                dlc=8,
                data=rx_msg.payload,
            )
            return msg, False
        return None, False

    def send(self, msg, timeout=None):
        txMsg = simply.Message(msg.arbitration_id, msg.data)

        # Log errors for now - low level driver does not throw exceptions on failed comms or disconnections
        try:
            simply.send(txMsg)
        except Exception as e:
            logger.error("Exception on SimplycanBus.send")
            raise

    def shutdown(self):
        super(SimplycanBus, self).shutdown()
        simply.close()
