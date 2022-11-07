import logging
from typing import List, Tuple

from uds.uds_config_tool import DecodeFunctions
from uds.uds_config_tool.odx.diag_coded_types import (DiagCodedType,
                                                      MinMaxLengthType,
                                                      StandardLengthType)


class PosResponse():
    """encapsulates diagCodedType and DID information for parsing uds response
    """

    def __init__(self, diagCodedType: DiagCodedType, didLength: int, DID: int) -> None:
        self.diagCodedType = diagCodedType
        self.didLength = didLength
        self.DID = DID
        logging.info(f"self.didLength: {self.didLength}")
        logging.info(f"self.diagCodedType: {self.diagCodedType}")

    # TODO:
    def parse(self, DIDResponse: List[int]) -> str:
        """Parse a (partial) response of a DID
        """
        # remove the did before parsing -> insert DID check here?
        toParse = DIDResponse[self.didLength: ]
        # remove termination char if exists:
        if isinstance(self.diagCodedType, MinMaxLengthType):
            toParse = toParse[ :-1]
        encodingType = self.diagCodedType.base_data_type
        if encodingType == "A_ASCIISTRING":
            logging.info(f"Trying to decode A_ASCIISTRING:")
            parsedResponse = DecodeFunctions.intListToString(toParse, None)
        elif encodingType == "A_UINT32":
            logging.info(f"Trying to decode A_UINT32:")
        else:
            logging.info(f"Trying to decode another encoding type:")

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

    def __repr__(self):
        return f"{self.__class__.__name__}: diagCodedType={self.diagCodedType}, didLength={self.didLength}, DID={self.DID}"

    def __str__(self):
        return f"{self.__class__.__name__}: diagCodedType={self.diagCodedType}, didLength={self.didLength}, DID={self.DID}"
