from abc import ABC, abstractmethod
from enum import IntEnum
import logging
from typing import List


class DiagCodedType(ABC):
    """Base Class for all DIAG-CODED-TYPEs
    """

    def __init__(self, base_data_type: str) -> None:
        super().__init__()
        self.base_data_type = base_data_type


    @abstractmethod
    def calculateLength(self, response: List[int]) -> int:
        pass


class StandardLengthType(DiagCodedType):
    """Represents the DIAG-CODED-TYPE of a POS-RESPONSE with a static length
    """

    def __init__(self, base_data_type: str, bitLength: int) -> None:
        super().__init__(base_data_type)
        self.bitLength = bitLength

    def calculateLength(self, response: List[int]) -> int:
        """Returns the static length of StandardLengthType (excluding DID)
        """
        logging.info("Calculating length in standardLengthType")

        return self.bitLength

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.base_data_type}',{self.bitLength})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: base-data-type={self.base_data_type} length={self.bitLength}"


class MinMaxLengthType(DiagCodedType):
    """Represents the DIAG-CODED-TYPE of a POS-RESPONSE with dynamic length

    minLength or maxLength are None if they are not specified in the ODX file
    """

    class TerminationChar(IntEnum):
        ZERO = 0,
        HEX_FF = 255


    def __init__(self, base_data_type: str, minLength: int, maxLength: int, termination: str) -> None:
        super().__init__(base_data_type)
        self.minLength = minLength
        self.maxLength = maxLength
        self._termination = self._getTermination(termination)


    @staticmethod
    def _getTermination(termination):
        if termination == "ZERO":
            return MinMaxLengthType.TerminationChar.ZERO
        elif termination == "HEX-FF":
            return MinMaxLengthType.TerminationChar.HEX_FF
        else:
            # end-of-pdu: max or end of response -> need to check in length calculation (needs the response)
            return termination


    def calculateLength(self, response: List[int]) -> int:
        """Returns the dynamically calculated length of MinMaxLengthType from the response list 
        (excluding DID)
        """
        logging.info(f"passed response: {response}")
        # TODO: end-of-pdu handling: read till response end
        if self._termination != "END-OF-PDU":
            pass

        for dynamicLength, value in enumerate(response):
            logging.info(f"dynamicLength: {dynamicLength}, value: {value}")

            if value == self._termination and dynamicLength < self.minLength:
                raise ValueError(f"Response shorter than expected minimum")
            elif value == self._termination or dynamicLength == self.maxLength:
                logging.info(f"Found termination char {self._termination} or reached max length {self.maxLength}")
                logging.info(f"length at end condition: {dynamicLength}\n")
                # TODO: does it ALWAYS have a termination char, even if max length used? -> then need to handle separately:
                # + 1 for termination char, no + 1 for max length
                return dynamicLength + 1 # account for termination char with + 1
            elif dynamicLength > self.maxLength:
                raise ValueError(f"Response longer than expected max length")

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.base_data_type}', {self.minLength}, {self.maxLength}, {self._termination})"

    def __str__(self):
        return f"{self.__class__.__name__}: base-data-type={self.base_data_type}, min={self.minLength}, max={self.maxLength}, termination={self._termination}"

