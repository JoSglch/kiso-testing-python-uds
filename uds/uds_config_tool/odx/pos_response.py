import logging
from typing import Dict, List, Tuple

from uds.uds_config_tool import DecodeFunctions
from uds.uds_config_tool.odx.diag_coded_types import (MinMaxLengthType,
                                                      StandardLengthType)
from uds.uds_config_tool.odx.param import Param


class PosResponse():
    """encapsulates params and DID + SID information for parsing  a positive uds response
    """

    def __init__(self, param: Param, didLength: int, DID: int, sidLength: int, SID: int) -> None:
        self.param = param
        self.didLength = didLength
        self.DID = DID
        self.sidLength = sidLength
        self.SID = SID

    # TODO: handle list of params
    def decode(self, DIDResponse: List[int]) -> Dict[str, str]:
        """Parse a response to a DID

        :param DIDResponse: response component for this PosResponse's DID
        :return: parsed response as string
        """
        # TODO: insert DID check here?
        toDecode = DIDResponse[self.didLength: ]
        # remove termination char, END-OF-PDU type has no termination char
        if isinstance(self.param.diagCodedType, MinMaxLengthType) and self.param.diagCodedType.termination.value != "END-OF-PDU":
            terminationCharLength = self.param.diagCodedType.getTerminationLength()
            toDecode = toDecode[ :-terminationCharLength]
        encodingType = self.param.diagCodedType.base_data_type
        if encodingType == "A_ASCIISTRING":
            logging.info(f"Trying to decode A_ASCIISTRING:")
            decodedResponse = DecodeFunctions.intListToString(toDecode, None)
            logging.info(f"decoded ascii: {decodedResponse}")
        elif encodingType == "A_UINT32":
            logging.info(f"Trying to decode A_UINT32:")
            # TODO: how to decode?
            decodedResponse = toDecode
            logging.info(f"decoded uint32: {decodedResponse}")
        else:
            logging.info(f"Trying to decode another encoding type:")
            # TODO: how to decode?
            raise NotImplementedError(f"Decoding of {encodingType} is not implemented yet")
        result = {self.param.short_name: decodedResponse}
        logging.info(f"Decoded result: {result}")

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
        return f"{self.__class__.__name__}: param={self.param}, didLength={self.didLength}, DID={self.DID}"
