#!/usr/bin/env python
# coding: utf-8

"""
Test for usbtin interface
"""

from unittest import TestCase, mock

import can
import pyusbtin
from can.interfaces.usbtin import USBtinBus


class TestUSBtinBus(TestCase):
    @mock.patch("can.interfaces.usbtin.pyusbtin.usbtin")
    def setUp(self, pyusbtin_usbtin):
        # setup the bus
        test_port = "test_port"
        test_baudrate = 100
        self.bus = bus = can.Bus(
            bustype="usbtin", channel=test_port, baudrate=test_baudrate
        )

        # test the bus
        self.assertEqual(bus.baudrate, test_baudrate)
        bus.usbtin.connect.assert_called_once_with(test_port)
        self.assertEqual(bus.channel_info, "usbtin")
        bus.usbtin.open_can_channel.assert_called_once_with(
            test_baudrate, pyusbtin.usbtin.USBtin.ACTIVE
        )
        bus.usbtin.add_message_listener.assert_called_once_with(bus._bridge_cb)

        # setup some test messages
        test_id = 1
        test_rtr = False
        test_dlc = 2
        test_data = [3, 4]
        self.test_can_message = can.Message(
            arbitration_id=test_id,
            is_remote_frame=test_rtr,
            dlc=test_dlc,
            data=bytearray(test_data),
        )
        self.test_pyusbtin_can_message = pyusbtin.canmessage.CANMessage(
            mid=test_id, dlc=test_dlc, data=test_data
        )

    def test_send(self):
        self.bus.send(self.test_can_message)

        # TODO: add addTypeEqualityFunc() to make things cleaner
        self.assertEqual(
            self.test_pyusbtin_can_message.mid, self.bus.usbtin.send.call_args[0][0].mid
        )
        self.assertEqual(
            self.test_pyusbtin_can_message.dlc, self.bus.usbtin.send.call_args[0][0].dlc
        )
        self.assertEqual(
            self.test_pyusbtin_can_message.rtr, self.bus.usbtin.send.call_args[0][0].rtr
        )
        self.assertEqual(
            self.test_pyusbtin_can_message._data,
            self.bus.usbtin.send.call_args[0][0]._data,
        )

    def test_shutdown(self):
        self.bus.shutdown()
        self.bus.usbtin.close_can_channel.assert_called_once()
        self.bus.usbtin.disconnect.assert_called_once()

    def test__recv_internal_empty_fifo(self):
        self.assertEqual(self.bus._recv_internal(0), (None, False))

    def test__recv_internal_fifo_with_entries(self):
        self.bus.rx_fifo = [self.test_pyusbtin_can_message]
        resp = self.bus._recv_internal(0)

        self.assertEqual(resp[0].arbitration_id, self.test_can_message.arbitration_id)
        self.assertEqual(resp[0].dlc, self.test_can_message.dlc)
        self.assertEqual(resp[0].is_remote_frame, self.test_can_message.is_remote_frame)
        self.assertEqual(resp[0].data, self.test_can_message.data)
        self.assertEqual(resp[1], False)
