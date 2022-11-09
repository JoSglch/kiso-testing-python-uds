#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"

import logging
import sys

from uds.uds_config_tool import DecodeFunctions
from uds.uds_config_tool.FunctionCreation.iServiceMethodFactory import \
    IServiceMethodFactory
from uds.uds_config_tool.odx.diag_coded_types import (DiagCodedType,
                                                      MinMaxLengthType,
                                                      StandardLengthType)
from uds.uds_config_tool.odx.globals import xsi
from uds.uds_config_tool.odx.pos_response import PosResponse
from uds.uds_config_tool.UtilityFunctions import (
    getDiagCodedTypeFromDop, getDiagCodedTypeFromStructure)

# Extended to cater for multiple DIDs in a request - typically rather than processing
# a whole response in one go, we break it down and process each part separately.
# We can cater for multiple DIDs by then combining whatever calls we need to.

requestSIDFuncTemplate = str("def {0}():\n" "    return {1}")
requestDIDFuncTemplate = str("def {0}():\n" "    return {1}")

negativeResponseFuncTemplate = str(
    "def {0}(input):\n"
    "    result = {{}}\n"
    "    nrcList = {5}\n"
    "    if input[{1}:{2}] == [{3}]:\n"
    "        result['NRC'] = input[{4}]\n"
    "        result['NRC_Label'] = nrcList.get(result['NRC'])\n"
    "    return result"
)


##
# @brief this should be static
class ReadDataByIdentifierMethodFactory(IServiceMethodFactory):
    @staticmethod
    def create_requestFunctions(diagServiceElement, xmlElements):

        serviceId = 0
        diagnosticId = 0

        shortName = "request_{0}".format(diagServiceElement.find("SHORT-NAME").text)
        requestSIDFuncName = "requestSID_{0}".format(shortName)
        requestDIDFuncName = "requestDID_{0}".format(shortName)
        requestElement = xmlElements[
            diagServiceElement.find("REQUEST-REF").attrib["ID-REF"]
        ]
        paramsElement = requestElement.find("PARAMS")
        for param in paramsElement:
            semantic = None
            try:
                semantic = param.attrib["SEMANTIC"]
            except AttributeError:
                pass

            if semantic == "SERVICE-ID":
                serviceId = [int(param.find("CODED-VALUE").text)]
            elif semantic == "ID":
                diagnosticId = DecodeFunctions.intArrayToIntArray(
                    [int(param.find("CODED-VALUE").text)], "int16", "int8"
                )

        funcString = requestSIDFuncTemplate.format(
            requestSIDFuncName, serviceId  # 0
        )  # 1
        exec(funcString)

        funcString = requestDIDFuncTemplate.format(
            requestDIDFuncName, diagnosticId  # 0
        )  # 1
        exec(funcString)

        return (locals()[requestSIDFuncName], locals()[requestDIDFuncName])

    @staticmethod
    def create_checkPositiveResponseFunctions(diagServiceElement, xmlElements):
        logging.info(f"----- create_checkPositiveResponseFunctions() -----")
        responseId = 0
        diagnosticId = 0

        responseIdStart = 0
        responseIdEnd = 0
        diagnosticIdStart = 0
        diagnosticIdEnd = 0

        shortName = diagServiceElement.find("SHORT-NAME").text
        checkSIDRespFuncName = "checkSIDResp_{0}".format(shortName)
        checkSIDLenFuncName = "checkSIDLen_{0}".format(shortName)
        checkDIDRespFuncName = "checkDIDResp_{0}".format(shortName)
        positiveResponseElement = xmlElements[
            (diagServiceElement.find("POS-RESPONSE-REFS"))
            .find("POS-RESPONSE-REF")
            .attrib["ID-REF"]
        ]
        logging.info(positiveResponseElement.find("SHORT-NAME").text)
        paramsElement = positiveResponseElement.find("PARAMS")

        SIDLength = 0
        DIDLength = 0
        diagCodedType: DiagCodedType = None  # not needed?

        for param in paramsElement:
            try:
                semantic = None
                try:
                    semantic = param.attrib["SEMANTIC"]
                except AttributeError:
                    pass

                if semantic == "SERVICE-ID":
                    logging.info("PARAM: SID")
                    responseId = int(param.find("CODED-VALUE").text)
                    bitLength = int(
                        (param.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                    )
                    listLength = int(bitLength / 8)
                    SIDLength = listLength
                    logging.info(f"SIDLength: {SIDLength}")
                elif semantic == "ID":
                    logging.info("PARAM: ID")
                    diagnosticId = int(param.find("CODED-VALUE").text)
                    bitLength = int(
                        (param.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                    )
                    listLength = int(bitLength / 8)
                    DIDLength = listLength
                    logging.info(f"DIDLength: {DIDLength}")
                elif semantic == "DATA":
                    # TODO: create the diagCodedType in this condition
                    logging.info("PARAM: DATA")
                    dataObjectElement = xmlElements[
                        (param.find("DOP-REF")).attrib["ID-REF"]
                    ]
                    if dataObjectElement.tag == "DATA-OBJECT-PROP":
                        # TODO: DOP handling
                        diagCodedType = getDiagCodedTypeFromDop(dataObjectElement)

                    elif dataObjectElement.tag == "STRUCTURE":
                        diagCodedType = getDiagCodedTypeFromStructure(dataObjectElement, xmlElements)

                    else:
                        # neither DOP nor STRUCTURE
                        pass
                else:
                    # not a PARAM with SID, ID (= DID), or DATA
                    pass
            except:
                logging.warning(sys.exc_info())
                pass

        # instead of checkDIDLenFunc and all the others (also can get rid of other check functions):
        posResponse = PosResponse(diagCodedType, DIDLength, diagnosticId, SIDLength, responseId)
        logging.info(f"posResponse: {posResponse}")
        return posResponse


    @staticmethod
    def create_checkNegativeResponseFunction(diagServiceElement, xmlElements):

        shortName = diagServiceElement.find("SHORT-NAME").text
        check_negativeResponseFunctionName = "check_negResponse_{0}".format(shortName)

        negativeResponsesElement = diagServiceElement.find("NEG-RESPONSE-REFS")

        negativeResponseChecks = []

        for negativeResponse in negativeResponsesElement:
            negativeResponseRef = xmlElements[negativeResponse.attrib["ID-REF"]]

            negativeResponseParams = negativeResponseRef.find("PARAMS")

            for param in negativeResponseParams:

                semantic = None
                try:
                    semantic = param.attrib["SEMANTIC"]
                except:
                    semantic = None

                bytePosition = int(param.find("BYTE-POSITION").text)

                if semantic == "SERVICE-ID":
                    serviceId = param.find("CODED-VALUE").text
                    start = int(param.find("BYTE-POSITION").text)
                    diagCodedType = param.find("DIAG-CODED-TYPE")
                    bitLength = int(
                        (param.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                    )
                    listLength = int(bitLength / 8)
                    end = start + listLength
                elif bytePosition == 2:
                    nrcPos = bytePosition
                    expectedNrcDict = {}
                    try:
                        dataObjectElement = xmlElements[
                            (param.find("DOP-REF")).attrib["ID-REF"]
                        ]
                        nrcList = (
                            dataObjectElement.find("COMPU-METHOD")
                            .find("COMPU-INTERNAL-TO-PHYS")
                            .find("COMPU-SCALES")
                        )
                        for nrcElem in nrcList:
                            expectedNrcDict[int(nrcElem.find("LOWER-LIMIT").text)] = (
                                nrcElem.find("COMPU-CONST").find("VT").text
                            )
                    except:
                        pass
                pass

        negativeResponseFunctionString = negativeResponseFuncTemplate.format(
            check_negativeResponseFunctionName,
            start,
            end,
            serviceId,
            nrcPos,
            expectedNrcDict,
        )

        exec(negativeResponseFunctionString)
        return locals()[check_negativeResponseFunctionName]
