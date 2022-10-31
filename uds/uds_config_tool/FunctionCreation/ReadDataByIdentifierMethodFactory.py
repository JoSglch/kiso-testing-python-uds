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

# Extended to cater for multiple DIDs in a request - typically rather than processing
# a whole response in one go, we break it down and process each part separately.
# We can cater for multiple DIDs by then combining whatever calls we need to.

requestSIDFuncTemplate = str("def {0}():\n" "    return {1}")
requestDIDFuncTemplate = str("def {0}():\n" "    return {1}")

checkSIDRespFuncTemplate = str(
    "def {0}(input):\n"
    "    serviceIdExpected = {1}\n"
    "    serviceId = DecodeFunctions.buildIntFromList(input[{2}:{3}])\n"
    '    if(serviceId != serviceIdExpected): raise Exception("Service Id Received not expected. Expected {{0}}; Got {{1}} ".format(serviceIdExpected, serviceId))'
)

checkSIDLenFuncTemplate = str("def {0}():\n" "    return {1}")

checkDIDRespFuncTemplate = str(
    "def {0}(input):\n"
    "    diagnosticIdExpected = {1}\n"
    "    diagnosticId = DecodeFunctions.buildIntFromList(input[{2}:{3}])\n"
    '    if(diagnosticId != diagnosticIdExpected): raise Exception("Diagnostic Id Received not as expected. Expected: {{0}}; Got {{1}}".format(diagnosticIdExpected, diagnosticId))'
)

checkDIDLenFuncTemplate = str(
    "def {0}():\n"
    "    logging.info('{0}')\n"
    "    logging.info('{1}')\n"
    "    return {1}"
)

negativeResponseFuncTemplate = str(
    "def {0}(input):\n"
    "    result = {{}}\n"
    "    nrcList = {5}\n"
    "    if input[{1}:{2}] == [{3}]:\n"
    "        result['NRC'] = input[{4}]\n"
    "        result['NRC_Label'] = nrcList.get(result['NRC'])\n"
    "    return result"
)

encodePositiveResponseFuncTemplate = str(
    "def {0}(input,offset):\n"
    "    result = {{}}\n"
    "    logging.info('{0}')\n"
    "    logging.info('input:')\n"
    "    logging.info(input)\n"
    "    logging.info('offset:')\n"
    "    logging.info(offset)\n"
    "    {1}\n"
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
        logging.debug("--- create_checkPositiceResponseFunctions ---")
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
        checkDIDLenFuncName = "checkDIDLen_{0}".format(shortName)
        positiveResponseElement = xmlElements[
            (diagServiceElement.find("POS-RESPONSE-REFS"))
            .find("POS-RESPONSE-REF")
            .attrib["ID-REF"]
        ]
        logging.info(positiveResponseElement.find("SHORT-NAME").text)
        paramsElement = positiveResponseElement.find("PARAMS")

        totalLength = 0
        SIDLength = 0

        for param in paramsElement:
            try:
                semantic = None
                try:
                    semantic = param.attrib["SEMANTIC"]
                except AttributeError:
                    pass

                startByte = int(param.find("BYTE-POSITION").text)

                if semantic == "SERVICE-ID":
                    logging.debug("PARAM: SID")
                    responseId = int(param.find("CODED-VALUE").text)
                    bitLength = int(
                        (param.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                    )
                    listLength = int(bitLength / 8)
                    responseIdStart = startByte
                    responseIdEnd = startByte + listLength
                    totalLength += listLength
                    SIDLength = listLength
                elif semantic == "ID":
                    logging.debug("PARAM: ID")
                    diagnosticId = int(param.find("CODED-VALUE").text)
                    bitLength = int(
                        (param.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                    )
                    listLength = int(bitLength / 8)
                    diagnosticIdStart = startByte
                    diagnosticIdEnd = startByte + listLength
                    totalLength += listLength
                elif semantic == "DATA":
                    logging.debug("PARAM: DATA")
                    dataObjectElement = xmlElements[
                        (param.find("DOP-REF")).attrib["ID-REF"]
                    ]
                    if dataObjectElement.tag == "DATA-OBJECT-PROP":
                        logging.debug("DOP")
                        start = int(param.find("BYTE-POSITION").text)
                        bitLength = int(
                            dataObjectElement.find("DIAG-CODED-TYPE")
                            .find("BIT-LENGTH")
                            .text
                        )
                        logging.debug(f"bitlength: {bitLength}")
                        listLength = int(bitLength / 8)
                        totalLength += listLength
                        logging.debug(f"totalLength: {totalLength}")
                    elif dataObjectElement.tag == "STRUCTURE":
                        logging.debug("DOP")
                        start = int(param.find("BYTE-POSITION").text)
                        listLength = int(dataObjectElement.find("BYTE-SIZE").text)
                        logging.debug(f"bitlength: {bitLength}")
                        totalLength += listLength
                        logging.debug(f"totalLength: {totalLength}")
                    else:
                        pass
                else:
                    pass
            except:
                logging.warning(sys.exc_info())
                pass

        checkSIDRespFuncString = checkSIDRespFuncTemplate.format(
            checkSIDRespFuncName,  # 0
            responseId,  # 1
            responseIdStart,  # 2
            responseIdEnd,
        )  # 3
        logging.debug(f"checkSIDRespFuncString: {checkSIDRespFuncString}")
        exec(checkSIDRespFuncString)
        checkSIDLenFuncString = checkSIDLenFuncTemplate.format(
            checkSIDLenFuncName, SIDLength  # 0
        )  # 1
        logging.debug(f"checkSIDLenFuncString: {checkSIDLenFuncString}")
        exec(checkSIDLenFuncString)
        checkDIDRespFuncString = checkDIDRespFuncTemplate.format(
            checkDIDRespFuncName,  # 0
            diagnosticId,  # 1
            diagnosticIdStart
            - SIDLength,  # 2... note: we no longer look at absolute pos in the response,
            diagnosticIdEnd - SIDLength,
        )  # 3      but look at the DID response as an isolated extracted element.
        logging.debug(f"checkDIDRespFuncString: {checkDIDRespFuncString}")
        exec(checkDIDRespFuncString)
        checkDIDLenFuncString = checkDIDLenFuncTemplate.format(
            checkDIDLenFuncName, totalLength - SIDLength  # 0
        )  # 1
        logging.debug(f"checkDIDLenFuncString {checkDIDLenFuncString}")
        exec(checkDIDLenFuncString)

        return (
            locals()[checkSIDRespFuncName],
            locals()[checkSIDLenFuncName],
            locals()[checkDIDRespFuncName],
            locals()[checkDIDLenFuncName],
        )

    ##
    # @brief may need refactoring to deal with multiple positive-responses (WIP)
    @staticmethod
    def create_encodePositiveResponseFunction(diagServiceElement, xmlElements):
        logging.debug("---- create_encodePositiveResponseFunction ---")
        positiveResponseElement = xmlElements[
            (diagServiceElement.find("POS-RESPONSE-REFS"))
            .find("POS-RESPONSE-REF")
            .attrib["ID-REF"]
        ]

        shortName = diagServiceElement.find("SHORT-NAME").text
        encodePositiveResponseFunctionName = "encode_{0}".format(shortName)
        logging.info(f"{shortName}")
        params = positiveResponseElement.find("PARAMS")

        encodeFunctions = []

        for param in params:
            try:
                semantic = None
                try:
                    semantic = param.attrib["SEMANTIC"]
                except AttributeError:
                    pass

                if semantic == "DATA":
                    logging.debug("PARAM: DATA")
                    dataObjectElement = xmlElements[
                        (param.find("DOP-REF")).attrib["ID-REF"]
                    ]
                    longName = param.find("LONG-NAME").text
                    logging.debug(f"DOP: {longName}")
                    bytePosition = int(param.find("BYTE-POSITION").text)
                    bitLength = int(
                        dataObjectElement.find("DIAG-CODED-TYPE")
                        .find("BIT-LENGTH")
                        .text
                    )
                    logging.debug(f"bitLength: {bitLength}")
                    listLength = int(bitLength / 8)
                    logging.debug(f"listLength: {listLength}")
                    endPosition = bytePosition + listLength
                    logging.debug(f"endPosition: {endPosition}")
                    encodingType = dataObjectElement.find("DIAG-CODED-TYPE").attrib[
                        "BASE-DATA-TYPE"
                    ]
                    if (encodingType) == "A_ASCIISTRING":
                        functionString = "DecodeFunctions.intListToString(input[{0}-offset:{1}-offset], None)".format(
                            bytePosition, endPosition
                        )
                    elif encodingType == "A_UINT32":
                        functionString = "input[{1}-offset:{2}-offset]".format(
                            longName, bytePosition, endPosition
                        )
                    else:
                        functionString = "input[{1}-offset:{2}-offset]".format(
                            longName, bytePosition, endPosition
                        )
                    logging.debug(f"functionString: {functionString}")
                    encodeFunctions.append(
                        "result['{0}'] = {1}".format(longName, functionString)
                    )
            except:
                logging.warning(sys.exc_info())
                pass

        encodeFunctionString = encodePositiveResponseFuncTemplate.format(
            encodePositiveResponseFunctionName, "\n    ".join(encodeFunctions)
        )
        logging.debug(f"encodeFunctionString: {encodeFunctionString}")
        exec(encodeFunctionString)
        return locals()[encodePositiveResponseFunctionName]

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
