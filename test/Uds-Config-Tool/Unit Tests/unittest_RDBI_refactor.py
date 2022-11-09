import unittest
from pathlib import Path
from unittest import mock
from uds.config import Config

from uds.uds_communications.Uds.Uds import Uds
from uds.uds_config_tool.UdsConfigTool import UdsTool


class RDBIRefactorTest(unittest.TestCase):

    def test_RDBI(self):

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

        b = uds.readDataByIdentifier(
            ["ECU Serial Number", "Boot Software Identification"]
        )
        self.assertIsInstance(uds, Uds)


if __name__ == '__main__':
    unittest.main()