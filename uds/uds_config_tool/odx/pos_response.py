import logging
from typing import Dict, List, Tuple

from uds.uds_config_tool import DecodeFunctions
from uds.uds_config_tool.odx.diag_coded_types import (MinMaxLengthType,
                                                      StandardLengthType)
from uds.uds_config_tool.odx.param import Param


class PosResponse():
    """encapsulates params and DID + SID information for parsing  a positive uds response
    """

    def __init__(self, params: List[Param], didLength: int, DID: int, sidLength: int, SID: int) -> None:
        self.params = params
        self.didLength = didLength
        self.DID = DID
        self.sidLength = sidLength
        self.SID = SID

    # TODO: handle list of params
    def decode(self, DIDResponse: List[int]) -> Dict[str, str]:
        """Parse a response to a DID

        :param DIDResponse: response component for this PosResponse's DID
        :return: dictionary of parsed responses with short name as key
        """
        result = {}
        # maybe add DID check here?
        for param in self.params:
            result[param.short_name] = param.decode()
            logging.info(f"Decoded result: {result}")
        return result

    def parseDIDResponseComponent(self, response: List[int]) -> List[int]:
        """parses the response component that contains this PosResponses data of the complete response
        """
        # safe the data for each param in the param here instead of returning a list?
        logging.info(f"getDIDResponseComp: response {response}")
        startPosition = self.didLength
        endPosition = self.didLength
        for param in self.params:
            logging.info(f"startposition: {startPosition}")
            toParse = response[startPosition: ]
            logging.info(f"toParse in loop: {toParse}")
            paramLength = param.calculateLength(toParse)
            logging.info(f"calculated length: {paramLength}")
            endPosition += paramLength
            logging.info(f"endPosition: {endPosition}")
            data = response[startPosition: endPosition]
            logging.info(f"data: {data}")
            param.data = data
            logging.info(f"param with data: {param}")
            startPosition = endPosition
        result = response[:endPosition]
        logging.info(f"calculated response comp: {result}")
        return result

    def checkDIDInResponse(self, didResponse: List[int]) -> None:
        """compare PosResponse's DID with the DID at beginning of a response
        """
        logging.info(f"Check beginning of passed response for DID")
        actualDID = DecodeFunctions.buildIntFromList(didResponse[:self.didLength])
        if self.DID != actualDID:
            raise AttributeError(f"The expected DID {self.DID} does not match the received DID {actualDID}")


    def checkSIDInResponse(self, response: List[int]) -> None:
        """compare PosResponse's SID with the SID at beginning of a response
        """
        actualSID = DecodeFunctions.buildIntFromList(response[:self.sidLength])
        if self.SID != actualSID:
            raise AttributeError(f"The expected SID {self.SID} does not match the received SID {actualSID}")


    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: param={self.params}, didLength={self.didLength}, DID={self.DID}"
