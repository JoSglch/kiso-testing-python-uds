import unittest
from pathlib import Path
from unittest import mock

from uds.config import Config
from uds.uds_communications.TransportProtocols.Can.CanTp import CanTp
from uds.uds_communications.Uds.Uds import Uds


class RDBIRefactorTest(unittest.TestCase):

    def setUp(self):
        self.here = Path(__file__).parent

        self.DEFAULT_UDS_CONFIG = {
            "transport_protocol": "CAN",
            "p2_can_client": 5,
            "p2_can_server": 1,
        }
        self.DEFAULT_TP_CONFIG = {
            "addressing_type": "NORMAL",
            "n_sa": 0xFF,
            "n_ta": 0xFF,
            "n_ae": 0xFF,
            "m_type": "DIAGNOSTICS",
            "discard_neg_resp": False,
        }
        self.DEFAULT_TP_CONFIG["req_id"] = 0xb0
        self.DEFAULT_TP_CONFIG["res_id"] = 0xb1


    @mock.patch("uds.uds_communications.TransportProtocols.Can.CanTp.CanTp.send")
    @mock.patch("uds.uds_communications.TransportProtocols.Can.CanTp.CanTp.recv")
    def test_RDBI_standardLength(self, tp_recv, tp_send):
        filename = "Bootloader.odx"
        odxFile = self.here.joinpath(filename)

        tp_send.return_value = False
        # ECU Serial Number = "ABC0011223344556"   (16 bytes as specified in "_Bootloader_87")
        tp_recv.return_value = [
            0x62,
            0xF1,
            0x8C,
            0x41,
            0x42,
            0x43,
            0x30,
            0x30,
            0x31,
            0x31,
            0x32,
            0x32,
            0x33,
            0x33,
            0x34,
            0x34,
            0x35,
            0x35,
            0x36,
        ]
        expected = "ABC0011223344556"

        Config.load_com_layer_config(self.DEFAULT_TP_CONFIG, self.DEFAULT_UDS_CONFIG)
        uds = Uds(odxFile)

        # for fixing the test:
        # self.assertIsInstance(uds, Uds)
        # self.assertEqual(uds._Uds__transportProtocol, "CAN")
        # self.assertIsInstance(uds.tp, CanTp)
        # self.assertTrue(hasattr(uds, "readDataByIdentifier"))
        # self.assertTrue(callable(uds.readDataByIdentifier))
        # self.assertTrue(hasattr(uds.tp, "recv"))

        actual = uds.readDataByIdentifier("ECU Serial Number")

        tp_send.assert_called_with([0x22, 0xF1, 0x8C], False, 0.01)
        self.assertEqual(expected, actual)


    # TODO: MinMaxLengthType
    @mock.patch("uds.uds_communications.TransportProtocols.Can.CanTp.CanTp.send")
    @mock.patch("uds.uds_communications.TransportProtocols.Can.CanTp.CanTp.recv")
    def test_RDBI_minMaxLengthBoth(self, tp_recv, tp_send):
        odxFile = self.here.joinpath("minimalexample.odx")
        tp_send.return_value = False
        # DID: 660 => 0x2 0x94 Termination: "Zero" Min: 1 Max: 15 Data: ABC0011223344
        tp_recv.return_value = [
            0x62, # SID
            0x02, # DID
            0x94, # DID
            0x41, # DATA ...
            0x42,
            0x43,
            0x30,
            0x30,
            0x31,
            0x31,
            0x32,
            0x32,
            0x33,
            0x33,
            0x34,
            0x34,
            0x00 # Termination Char
        ]
        expected = "ABC0011223344"
        Config.load_com_layer_config(self.DEFAULT_TP_CONFIG, self.DEFAULT_UDS_CONFIG)
        uds = Uds(odxFile)

        actual = uds.readDataByIdentifier("Dynamic_PartNumber")

        tp_send.assert_called_with([0x22, 0x02, 0x94], False, 0.01)
        self.assertEqual(expected, actual)

    # def test_RDBI_minMaxLengthOnlyMin():
    #     pass


    # def test_RDBI_minMaxLengthOnlyMax():
    #     pass


    # # TODO: more than one DID
    # def test_RDBI_MultipleDIDS():
    #     pass

    # def test_RDBI_negResponse():
    #     pass


if __name__ == '__main__':
    unittest.main()