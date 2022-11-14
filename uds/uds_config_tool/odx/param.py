import logging
from typing import List

from uds.uds_config_tool import DecodeFunctions
from uds.uds_config_tool.odx.diag_coded_types import (DiagCodedType,
                                                      MinMaxLengthType)


class Param():

    def __init__(self, short_name: str, byte_position: int, diagCodedType: DiagCodedType, data = None):
        self.short_name = short_name
        self.byte_position = byte_position
        self.diagCodedType = diagCodedType
        self.data = data

    def calculateLength(self, response: List[int]) -> int:
        return self.diagCodedType.calculateLength(response)

    def decode(self) -> str:
        """decode internal data that is set after parsing a uds response
        """
        if self.data is None:
            raise ValueError(f"Data in param is None, check if data DID response was parsed correctly")
        # there is data to decode
        toDecode = self.data
        # remove termination char, END-OF-PDU type has no termination char
        if isinstance(self.diagCodedType, MinMaxLengthType) and self.diagCodedType.termination.value != "END-OF-PDU":
            terminationCharLength = self.diagCodedType.getTerminationLength()
            toDecode = self.data[ :-terminationCharLength]
        encodingType = self.diagCodedType.base_data_type
        if encodingType == "A_ASCIISTRING":
            logging.info(f"Trying to decode A_ASCIISTRING:")
            decodedResponse = DecodeFunctions.intListToString(toDecode, None)
            logging.info(f"decoded ascii: {decodedResponse}")
        elif encodingType == "A_UINT32":
            logging.info(f"Trying to decode A_UINT32:")
            # TODO: is there decoding needed?
            decodedResponse = toDecode
            logging.info(f"decoded uint32: {decodedResponse}")
        else:
            logging.info(f"Trying to decode another encoding type:")
            # TODO: is there decoding needed?
            decodedResponse = toDecode
            logging.info(f"other decodedResponse: {decodedResponse}")
        return decodedResponse

    def __repr__(self):
        return f"{self.__class__.__name__}: short_name={self.short_name}, byte_position={self.byte_position}, \
            diagCodedType={self.diagCodedType}, data={self.data}"