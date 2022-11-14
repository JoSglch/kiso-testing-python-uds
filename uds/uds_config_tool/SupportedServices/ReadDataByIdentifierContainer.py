#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"


import logging
from types import MethodType
from typing import List

from uds.uds_config_tool.odx.pos_response import PosResponse
from uds.uds_config_tool.SupportedServices.iContainer import iContainer


class ReadDataByIdentifierContainer(object):

    __metaclass__ = iContainer

    def __init__(self):

        # To cater for lists we may have to re-factor here - i.e. requestFunc can be split into
        # requestSIDFunc and requestDIDFunc to allow building on the fly from a DID list
        # Negative response function is ok as it it

        self.requestSIDFunctions = {}
        self.requestDIDFunctions = {}

        self.posResponseObjects = {}

        self.negativeResponseFunctions = {}

    ##
    # @brief this method is bound to an external Uds object so that it call be called
    # as one of the in-built methods. uds.readDataByIdentifier("something") It does not operate
    # on this instance of the container class.
    @staticmethod
    def __readDataByIdentifier(target, parameter):
        logging.debug(f"===== readDataByIdentifier({target}, {parameter}) =====")
        # Some local functions to deal with use concatenation of a number of DIDs in RDBI operation ...

        # just want to know about the next bit of the response, so this pops it of the front of the response
        def popResponseElement(input, expectedResponseList: List[PosResponse]):
            """Parses the response into partial response for each DID
            """
            if expectedResponseList == []:
                raise Exception(
                    "Total length returned not as expected. Missing elements."
                )
            result = None
            # take the next PosResponse and its DIDResponseComponent
            DIDResponseComponent: List[int] = expectedResponseList[0].parseDIDResponseComponent(input)
            length = len(DIDResponseComponent)
            result = (
                DIDResponseComponent,
                input[length:],
                expectedResponseList[1:]
            )
            return result

        dids: str | List[str] = parameter
        if type(dids) is not list:
            dids = [dids]
        logging.debug(f"List of dids: {dids}")
        # Adding acceptance of lists at this point, as the spec allows for multiple rdbi request to be concatenated ...
        requestSIDFunction = target.readDataByIdentifierContainer.requestSIDFunctions[
            dids[0]
        ]  # ... the SID should be the same for all DIDs, so just use the first
        requestDIDFunctions = [
            target.readDataByIdentifierContainer.requestDIDFunctions[did]
            for did in dids
        ]
        expectedResponseObjects: List[PosResponse] = [
            target.readDataByIdentifierContainer.posResponseObjects[did]
            for did in dids
        ]
        logging.debug(f"expectedResponseObjects per did: {expectedResponseObjects}")
        # This is the same for all RDBI responses, irrespective of list or single input
        negativeResponseFunction = (
            target.readDataByIdentifierContainer.negativeResponseFunctions[dids[0]]
        )  # ... single code irrespective of list use, so just use the first

        # Call the sequence of functions to execute the RDBI request/response action ...
        # ==============================================================================

        # Create the request ...
        request = requestSIDFunction()
        for didFunc in requestDIDFunctions:
            request += didFunc()  # ... creates an array of integers
        logging.debug(f"uds request: {request}")
        # Send request and receive the response ...
        response = target.send(
            request
        )  # ... this returns a single response which may cover 1 or more DID response values
        logging.debug(f"uds response: {response}")
        negativeResponse = negativeResponseFunction(
            response
        )  # ... return nrc value if a negative response is received
        if negativeResponse:
            return negativeResponse
        logging.debug("----- Start response parsing ------")
        # We have a positive response so check that it makes sense to us ...
        # SID is the same for all expected PosResponses, just take the first
        expectedResponseObjects[0].checkSIDInResponse(response)
        SIDLength = expectedResponseObjects[0].sidLength
        logging.debug(f"SIDLength: {SIDLength}")
        # remove SID from response for further parsing the response per DID/ PosResponse
        responseRemaining = response[SIDLength:]
        # TODO: refactor this? DIDresponses/ DIDResponseComponents not needed for decoding anymore
        expectedResponses = expectedResponseObjects[:]  # copy
        DIDresponses: List[List[int]] = []
        for i in range(len(expectedResponseObjects)):
            (
                DIDResponseComponent,
                responseRemaining,
                expectedResponses,
            ) = popResponseElement(responseRemaining, expectedResponses)
            expectedResponseObjects[i].checkDIDInResponse(DIDResponseComponent)
            DIDresponses.append(DIDResponseComponent)
        logging.debug(f"Parsed partial response per DID: {DIDresponses}")
        # All is still good, so return the response ...
        logging.debug("----- Start response decoding ------")
        logging.debug(f"Response Types after Parsing: {expectedResponseObjects}")
        returnValue = tuple(
            [
                expectedResponseObjects[i].decode()
                for i in range(len(DIDresponses))
            ]
        )

        if len(returnValue) == 1:
            returnValue = returnValue[
                0
            ]  # ...we only send back a tuple if there were multiple DIDs
        return returnValue

    def bind_function(self, bindObject):
        bindObject.readDataByIdentifier = MethodType(
            self.__readDataByIdentifier, bindObject
        )

    ##
    # @brief method to add function to container - requestSIDFunction handles the SID component of the request message
    # def add_requestFunction(self, aFunction, dictionaryEntry):
    def add_requestSIDFunction(self, aFunction, dictionaryEntry):
        self.requestSIDFunctions[dictionaryEntry] = aFunction

    ##
    # @brief method to add function to container - requestDIDFunction handles the 1 to N DID components
    # of the request message
    def add_requestDIDFunction(self, aFunction, dictionaryEntry):
        self.requestDIDFunctions[dictionaryEntry] = aFunction

    ##
    # @brief method to add object to container
    # handles return of the expected DID details length and the extraction of any
    # DID details in the response message fragment for the DID that require return
    def add_posResponseObject(self, aObject: PosResponse, dictionaryEntry: str):
        self.posResponseObjects[dictionaryEntry] = aObject

    ##
    # @brief method to add function to container - negativeResponseFunction handles the checking of all possible
    # negative response codes in the response message, raising the required exception
    def add_negativeResponseFunction(self, aFunction, dictionaryEntry):
        self.negativeResponseFunctions[dictionaryEntry] = aFunction


if __name__ == "__main__":

    pass
