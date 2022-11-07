from typing import List

from uds.uds_config_tool.odx.diag_coded_types import DiagCodedType


class PosResponse():
    """encapsulates diagCodedType and DID information for parsing uds response
    """

    def __init__(self,
        diagCodedType: DiagCodedType,
        didLength: int,
        DID: int,
    ) -> None:
        self.diagCodedType = diagCodedType,
        self.didLength = didLength,
        self.DID = DID

    def parse(self, DIDResponse: List[int]) -> str:
        """Parse a (partial) response of a DID
        """
        toParse = DIDResponse[self.didLength:]
        parsedResponse = self.diagCodedType.parse(toParse)
        return parsedResponse
