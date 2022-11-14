from typing import List

from uds.uds_config_tool.odx.diag_coded_types import DiagCodedType


class Param():

    def __init__(self, short_name: str, byte_position: int, diagCodedType: DiagCodedType):
        self.short_name = short_name
        self.byte_position = byte_position
        self.diagCodedType = diagCodedType

    def calculateLength(self, response: List[int]) -> int:
        return self.diagCodedType.calculateLength(response)

    def __repr__(self):
        return f"{self.__class__.__name__}: short_name={self.short_name}, byte_position={self.byte_position}, \
            diagCodedType={self.diagCodedType}"