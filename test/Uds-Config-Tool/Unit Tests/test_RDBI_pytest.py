from pathlib import Path

import pytest

from uds.config import Config
from uds.uds_communications.TransportProtocols.Can.CanTp import CanTp
from uds.uds_communications.Uds.Uds import Uds


@pytest.fixture
def default_tp_config():
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
    return DEFAULT_TP_CONFIG

@pytest.fixture
def default_uds_config():
    DEFAULT_UDS_CONFIG = {
        "transport_protocol": "CAN",
        "p2_can_client": 5,
        "p2_can_server": 1,
    }
    return DEFAULT_UDS_CONFIG

def test_RDBI_staticLength(monkeypatch, default_tp_config, default_uds_config):

    here = Path(__file__).parent
    filename = "Bootloader.odx"
    odxFile = here.joinpath(filename)

    def mock_send(a,b,c,d):
        return False

    def mock_return(a,b):
        return [
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

    monkeypatch.setattr(CanTp, "send", mock_send)
    monkeypatch.setattr(CanTp, "recv", mock_return)

    Config.load_com_layer_config(default_tp_config, default_uds_config)
    uds = Uds(odxFile)

    actual = uds.readDataByIdentifier("ECU Serial Number")

    #mock_send.assert_called_with([0x22, 0xF1, 0x8C], False, 0.01)
    assert expected == actual

def test_RDBI_minMaxLength(monkeypatch, default_tp_config, default_uds_config):
    here = Path(__file__).parent
    odxFile = here.joinpath("minimalexample.odx")

    def mock_send(a,b,c,d):
        return False

    def mock_return(a,b):
        # DID: 660 => 0x2 0x94 Termination: "Zero" Min: 1 Max: 15 Data: ABC0011223344
        return [
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

    monkeypatch.setattr(CanTp, "send", mock_send)
    monkeypatch.setattr(CanTp, "recv", mock_return)


    Config.load_com_layer_config(default_tp_config, default_uds_config)
    uds = Uds(odxFile)

    actual = uds.readDataByIdentifier("Dynamic_PartNumber")

    # mock_send.assert_called_with([0x22, 0x02, 0x94], False, 0.01)
    assert expected == actual
