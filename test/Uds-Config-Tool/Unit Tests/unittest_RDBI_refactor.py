import unittest
from pathlib import Path
from unittest import mock

from uds.config import Config
from uds.uds_communications.Uds.Uds import Uds
from uds.uds_config_tool.SupportedServices.ReadDataByIdentifierContainer import ReadDataByIdentifierContainer
from uds.uds_config_tool.UdsConfigTool import UdsTool


class RDBIRefactorTest(unittest.TestCase):

    @mock.patch("uds.uds_communications.TransportProtocols.Can.CanTp")
    def test_RDBI(self, MockTp):

        here = Path(__file__).parent
        filename = "Bootloader.odx"
        filepath = here.joinpath(filename)

        DEFAULT_UDS_CONFIG = {
            "transport_protocol": "CAN",
            "p2_can_client": 5,
            "p2_can_server": 1,
        }
        DEFAULT_TP_CONFIG = {
            "addressing_type": "NORMAL",
            "n_sa": 0xFF,
            "n_ta": 0xFF,
            "n_ae": 0xFF,
            "m_type": "DIAGNOSTICS",
            "discard_neg_resp": False,
        }
        DEFAULT_TP_CONFIG["req_id"] = 0xb0
        DEFAULT_TP_CONFIG["res_id"] = 0xb1

        Config.load_com_layer_config(DEFAULT_TP_CONFIG, DEFAULT_UDS_CONFIG)
        uds = Uds(filepath)

        self.assertIsNotNone(uds)
        self.assertIsInstance(uds, Uds)

        MockTp.send.return_value = False
        # ECU Serial Number = "ABC0011223344556"   (16 bytes as specified in "_Bootloader_87")
        MockTp.recv.return_value = [
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

        b = uds.readDataByIdentifier(uds, "ECU Serial Number")



if __name__ == '__main__':
    unittest.main()