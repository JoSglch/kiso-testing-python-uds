from abc import ABC, abstractmethod
from enum import IntEnum
from typing import List


class DiagCodedType(ABC):
    """Base Class for all DIAG-CODED-TYPEs

    """

    def __init__(
            self,
            # base_data_type
        ) -> None:
        super().__init__()
        # self.base_data_type = base_data_type


    @abstractmethod
    def calculateLength(self, response: List[int]) -> int:
        pass


class StandardLengthType(DiagCodedType):
    """Represents the DIAG-CODED-TYPE of a POS-RESPONSE with a static length
    """

    def __init__(
            self,
            # base_data_type,
            bitLength
        ) -> None:
        super().__init__()
        self.bitLength = bitLength

    def calculateLength(self) -> int:
        """Returns the static length of StandardLengthType
        """
        print("Calculating length in standardLengthType")
        return self.bitLength

    def __repr__(self):
        return f"{self.__class__.__name__}: length={self.bitLength}"


class MinMaxLengthType(DiagCodedType):
    """Represents the DIAG-CODED-TYPE of a POS-RESPONSE with dynamic length
    """

    class TerminationChar(IntEnum):
        ZERO = 0,
        HEX_FF = 255


    def __init__(
            self,
            # base_data_type,
            minLength: int,
            maxLength: int,
            termination: str
        ) -> None:
        super().__init__()
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
        """
        print("calculating length in minMaxLengthType")
        print(f"passed response: {response}")
        # end-of-pdu handling
        if self._termination != "END-OF-PDU":
            pass

        for dynamicLength, value in enumerate(response):
            print(f"dynamicLength: {dynamicLength}, value: {value}")

            if value == self._termination and dynamicLength < self.minLength:
                raise ValueError(f"Response shorter than expected minimum")
            elif value == self._termination or dynamicLength == self.maxLength:
                print(f"Found termination char {self._termination} or reached max length {self.maxLength}")
                print(f"length at end condition: {dynamicLength}\n")
                # TODO: does it ALWAYS have a termination char, even if max length used? -> then need to handle separately:
                # + 1 for termination char, no + 1 for max length
                return dynamicLength + 1 # account for termination char with + 1
            elif dynamicLength > self.maxLength:
                raise ValueError(f"Response longer than expected max length")

    def __repr__(self):
        return f"{self.__class__.__name__}: min={self.minLength}, max={self.maxLength}, termination={self._termination}"
