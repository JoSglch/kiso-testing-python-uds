from uds.uds_config_tool.odx.diag_coded_types import DiagCodedType


class PosResponse():

    def __init__(self,
        diagCodedType: DiagCodedType,
        didLength: int,
        DID: int,
    ) -> None:
        self.diagCodedType = diagCodedType,
        self.didLength = didLength,
        self.DID = DID

    def parse():
        pass