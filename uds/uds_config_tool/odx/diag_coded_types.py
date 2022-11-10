import logging
from abc import ABC, abstractmethod
from enum import Enum
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
        return f"{self.__class__.__name__}: base-data-type={self.base_data_type} length={self.bitLength}"


class MinMaxLengthType(DiagCodedType):
    """Represents the DIAG-CODED-TYPE of a POS-RESPONSE with dynamic length

    minLength or maxLength are None if they are not specified in the ODX file
    """

    class TerminationChar(Enum):
        ZERO = 0
        HEX_FF = 255
        END_OF_PDU = "END-OF-PDU"


    def __init__(self, base_data_type: str, minLength: int, maxLength: int, termination: str) -> None:
        super().__init__(base_data_type)
        self.minLength = minLength
        self.maxLength = maxLength
        self.termination = self._getTermination(termination)


    @staticmethod
    def _getTermination(termination):
        if termination == "ZERO":
            return MinMaxLengthType.TerminationChar.ZERO
        elif termination == "HEX-FF":
            return MinMaxLengthType.TerminationChar.HEX_FF
        elif termination == "END-OF-PDU":
            return MinMaxLengthType.TerminationChar.END_OF_PDU
        else:
            raise ValueError(f"Termination {termination} found in .odx file is not valid")


    def calculateLength(self, response: List[int]) -> int:
        """Returns the dynamically calculated length of MinMaxLengthType from the response
        (excluding DID)
        """
        logging.info(f"passed response: {response}")
        if self.termination.value != "END-OF-PDU":
            # ends after max length, at end of response or after termination char
            for dynamicLength, value in enumerate(response):
                logging.info(f"dynamicLength: {dynamicLength}, value: {value}")
                if value == self.termination and dynamicLength < self.minLength:
                    raise ValueError(f"Response shorter than expected minimum")
                elif value == self.termination or dynamicLength == self.maxLength:
                    logging.info(f"Found termination char {self.termination} or reached max length {self.maxLength}")
                    logging.info(f"Length at end condition: {dynamicLength}")
                    # TODO: does it ALWAYS have a termination char, even if max length used? -> then need to handle separately:
                    # + 1 for termination char, no + 1 for max length
                    return dynamicLength + 1 # account for termination char with + 1
                elif self.maxLength is not None and dynamicLength > self.maxLength:
                    raise ValueError(f"Response longer than expected max length")
        # END-OF-PDU: response ends after max-length or at response end (?)
        else:
            if self.maxLength is None:
                return len(response)
            else:
                # TODO: go through response till end or max length
                raise NotImplementedError(f"Handle max-length here")


    def __repr__(self):
        return f"{self.__class__.__name__}: base-data-type={self.base_data_type}, min={self.minLength}, max={self.maxLength}, termination={self.termination}"
