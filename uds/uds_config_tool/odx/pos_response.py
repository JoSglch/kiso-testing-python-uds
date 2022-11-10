import logging
from typing import List, Tuple

from uds.uds_config_tool import DecodeFunctions
from uds.uds_config_tool.odx.diag_coded_types import (DiagCodedType,
                                                      MinMaxLengthType,
                                                      StandardLengthType)


class PosResponse():
    """encapsulates diagCodedType and DID information for parsing uds response
    """

    def __init__(self, diagCodedType: DiagCodedType, didLength: int, DID: int, sidLength: int, SID: int) -> None:
        self.diagCodedType = diagCodedType
        self.didLength = didLength
        self.DID = DID
        self.sidLength = sidLength
        self.SID = SID


    def parse(self, DIDResponse: List[int]) -> str:
        """Parse a response to a DID
        """
        # remove the did before parsing -> TODO: insert DID check here?
        toParse = DIDResponse[self.didLength: ]
        # remove termination char
        # TODO: make termination char length dynamic: 0 for endofpdu/  if its not END-OF-PDU type:
        if isinstance(self.diagCodedType, MinMaxLengthType) and self.diagCodedType.termination.value != "END-OF-PDU":
            terminationCharLength = self.diagCodedType.getTerminationLength()
            toParse = toParse[ :-terminationCharLength]
        encodingType = self.diagCodedType.base_data_type
        if encodingType == "A_ASCIISTRING":
            logging.info(f"Trying to decode A_ASCIISTRING:")
            parsedResponse = DecodeFunctions.intListToString(toParse, None)
        elif encodingType == "A_UINT32":
            logging.info(f"Trying to decode A_UINT32:")
            parsedResponse = toParse
        else:
            logging.info(f"Trying to decode another encoding type:")
            parsedResponse = toParse

        return parsedResponse


    def getTotalPossibleLength(self) -> Tuple[int, int]:
        """Return DIDLength + DATA length for range of poss byte lengths
        """
        totalMinLength = self.didLength
        totalMaxLength = self.didLength

        if isinstance(self.diagCodedType, StandardLengthType):
            totalMinLength += self.diagCodedType.bitLength
            totalMaxLength += self.diagCodedType.bitLength
        elif isinstance(self.diagCodedType, MinMaxLengthType):
            if self.diagCodedType.minLength is not None:
                totalMinLength += self.diagCodedType.minLength
            if self.diagCodedType.maxLength is not None:
                totalMaxLength += self.diagCodedType.maxLength

        return tuple([totalMinLength, totalMaxLength])


    def checkDID(self, didResponse: List[int]) -> None:
        logging.info(f"Check beginning of passed response for DID")
        actualDID = DecodeFunctions.buildIntFromList(didResponse[:self.didLength])
        if self.DID != actualDID:
            raise AttributeError(f"The expected DID {self.DID} does not match the received SID {actualDID}")


    def checkSID(self, response: List[int]) -> None:
        actualSID = DecodeFunctions.buildIntFromList(response[:self.sidLength])
        if self.SID != actualSID:
            raise AttributeError(f"The expected SID {self.SID} does not match the received SID {actualSID}")


    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: diagCodedType={self.diagCodedType}, didLength={self.didLength}, DID={self.DID}"
