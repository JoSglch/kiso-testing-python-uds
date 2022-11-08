import unittest
from pathlib import Path
from unittest import mock

from uds.uds_communications.Uds.Uds import Uds
from uds.uds_config_tool.UdsConfigTool import UdsTool


class RDBIRefactorTest(unittest.TestCase):

    def test_RDBI(self):

        here = Path(__file__).parent
        filename = "Bootloader.odx"
        filepath = here.joinpath(filename)

        uds = Uds(odx=filepath)  # create_service_container bound here



if __name__ == '__main__':
    unittest.main()