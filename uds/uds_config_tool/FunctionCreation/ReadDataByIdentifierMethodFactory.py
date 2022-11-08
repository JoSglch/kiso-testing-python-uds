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
from uds.uds_config_tool.UtilityFunctions import (findDescendant,
                                                  getDiagCodedTypeFromDop)
from uds.uds_config_tool.odx.pos_response import PosResponse

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
    "    logging.info('checkDIDLenFunc called for:')\n"
    "    logging.info('{0}')\n"
    '    exec("diagType = {1}")\n'
    "    return locals()['diagType']"
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
    "    logging.info('encodePositiveResponseFunction called')\n"
    "    result = {{}}\n"
    "    logging.info('{0}')\n"
    "    logging.info('input:')\n"
    "    logging.info(input)\n"
    "    logging.info('offset:')\n"
    "    logging.info(offset)\n"
    "    {1}\n"
    "    logging.info('result:')\n"
    "    logging.info(result)\n"
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
        DIDLength = 0
        diagCodedType: DiagCodedType = None

        for param in paramsElement:
            try:
                semantic = None
                try:
                    semantic = param.attrib["SEMANTIC"]
                except AttributeError:
                    pass

                startByte = int(param.find("BYTE-POSITION").text)

                if semantic == "SERVICE-ID":
                    logging.info("PARAM: SID")
                    responseId = int(param.find("CODED-VALUE").text)
                    bitLength = int(
                        (param.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                    )
                    listLength = int(bitLength / 8)
                    responseIdStart = startByte
                    responseIdEnd = startByte + listLength
                    totalLength += listLength
                    SIDLength = listLength
                    logging.info(f"totalLength: {totalLength}")
                elif semantic == "ID":
                    logging.info("PARAM: ID")
                    diagnosticId = int(param.find("CODED-VALUE").text)
                    bitLength = int(
                        (param.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                    )
                    listLength = int(bitLength / 8)
                    DIDLength = listLength
                    logging.info(f"DIDLength: {DIDLength}, type: {type(DIDLength)}")
                    diagnosticIdStart = startByte
                    diagnosticIdEnd = startByte + listLength
                    totalLength += listLength
                    logging.info(f"totalLength: {totalLength}")
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
                        logging.info("STRUCTURE")
                        # TODO: STATIC STRUCTURE
                        byteSizeElement = dataObjectElement.find("BYTE-SIZE")
                        if dataObjectElement.find("BYTE-SIZE") is not None:
                            logging.info(f"Static Length Structure...")
                            byteLength = int(byteSizeElement.text)
                            # get decoding info from first DOP, assume same decoding for each param
                            dop = xmlElements[
                                findDescendant("DOP-REF", dataObjectElement).attrib["ID-REF"]
                            ]
                            base_data_type = dop.find("DIAG-CODED-TYPE").attrib["BASE-DATA-TYPE"]
                            logging.info(f"base data type: {base_data_type}")
                            diagCodedType = StandardLengthType(base_data_type, byteLength)
                            logging.info(f"Created diagCodedType: {diagCodedType}, type: {type(diagCodedType)}")
                        # TODO: DYNAMIC STRUCTURE
                        else:
                            logging.info(f"Could not get BYTE-SIZE from STRUCTURE, checking for DOP-REF")
                            dopRef = findDescendant("DOP-REF", dataObjectElement)
                            if dopRef is None:
                                raise AttributeError("Could not find DOP from Structure, and no BYTE-SIZE: ODX probably invalid")

                            nestedDop = xmlElements[dopRef.attrib["ID-REF"]]
                            logging.info(f"dopRef= {dopRef}, dop= {nestedDop}")

                            logging.info("DATA OBJECT PROP from STRUCTURE...")
                            # TODO: STATIC DOP
                            base_data_type = nestedDop.find("DIAG-CODED-TYPE").attrib["BASE-DATA-TYPE"]
                            logging.info(f"base data type: {base_data_type}")
                            bitLengthElement = nestedDop.find("DIAG-CODED-TYPE").find("BIT-LENGTH")
                            if bitLengthElement is not None:
                                logging.info("Static Length DOP...")
                                bitLength = int(bitLengthElement.text)
                                logging.info(f"bitlength: {bitLength}")
                                byteLength = int(bitLength / 8)
                                diagCodedType = StandardLengthType(base_data_type, byteLength)
                                logging.info(f"Created diagCodedType: {diagCodedType}, type: {type(diagCodedType)}")
                            elif nestedDop.tag == "END-OF-PDU-FIELD":
                                # TODO: handle END-OF-PDU-FIELD
                                logging.warning(f"Found END-OF-PDU-FIELD")
                            # TODO: DYNAMIC DOP
                            else:
                                logging.info("Dynamic Length DOP...")
                                minLengthElement = nestedDop.find("DIAG-CODED-TYPE").find("MIN-LENGTH")
                                maxLengthElement = nestedDop.find("DIAG-CODED-TYPE").find("MAX-LENGTH")
                                logging.info(f"minLengthElement: {minLengthElement}, maxLengthElement: {maxLengthElement}")
                                minLength = None
                                maxLength = None
                                if minLengthElement is not None:
                                    minLength = int(minLengthElement.text)
                                if maxLengthElement is not None:
                                    maxLength = int(maxLengthElement.text)
                                logging.info(f"extracted dynamic lengths, min: {minLength}, max: {maxLength}")
                                termination = nestedDop.find("DIAG-CODED-TYPE").attrib["TERMINATION"]
                                diagCodedType = MinMaxLengthType(base_data_type, minLength, maxLength, termination)
                                logging.info(f"Created diagCodedType: {diagCodedType}, type: {type(diagCodedType)}")

                    else:
                        # neither DOP nor STRUCTURE
                        pass
                else:
                    # not a PARAM with SID, ID (= DID), or DATA
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
        logging.info(f"checkSIDRespFuncString: {checkSIDRespFuncString}")
        exec(checkSIDRespFuncString)
        checkSIDLenFuncString = checkSIDLenFuncTemplate.format(
            checkSIDLenFuncName, SIDLength  # 0
        )  # 1
        logging.info(f"checkSIDLenFuncString: {checkSIDLenFuncString}")
        exec(checkSIDLenFuncString)
        checkDIDRespFuncString = checkDIDRespFuncTemplate.format(
            checkDIDRespFuncName,  # 0
            diagnosticId,  # 1
            diagnosticIdStart
            - SIDLength,  # 2... note: we no longer look at absolute pos in the response,
            diagnosticIdEnd - SIDLength,
        )  # 3      but look at the DID response as an isolated extracted element.
        logging.info(f"checkDIDRespFuncString: {checkDIDRespFuncString}")
        exec(checkDIDRespFuncString)
        # instead of checkDIDLenFunc:
        logging.info(f"diagCodedType: {type(diagCodedType)}, ")
        posResponse: PosResponse = PosResponse(diagCodedType, DIDLength, diagnosticId)
        # logging.info(f"locals()['diagCodedType']: {locals()['diagCodedType']}")
        # logging.info(f"locals()['posResponse']: {locals()['posResponse']}")
        logging.info(f"posResponse: {posResponse}, type: {type(posResponse)}")
        return (
            locals()[checkSIDRespFuncName],
            locals()[checkSIDLenFuncName],
            locals()[checkDIDRespFuncName],
            posResponse
        )

    ##
    # @brief may need refactoring to deal with multiple positive-responses (WIP)
    @staticmethod
    def create_encodePositiveResponseFunction(diagServiceElement, xmlElements):
        logging.info("----- create_encodePositiveResponseFunction() -----")
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
                    logging.info("PARAM: DATA")
                    dataObjectElement = xmlElements[
                        (param.find("DOP-REF")).attrib["ID-REF"]
                    ]
                    longName = param.find("LONG-NAME").text
                    logging.info(f"DOP: {longName}")
                    bytePosition = int(param.find("BYTE-POSITION").text)
                    bitLength = int(
                        dataObjectElement.find("DIAG-CODED-TYPE")
                        .find("BIT-LENGTH")
                        .text
                    )
                    logging.info(f"bitLength: {bitLength}")
                    listLength = int(bitLength / 8)
                    logging.info(f"listLength: {listLength}")
                    endPosition = bytePosition + listLength
                    logging.info(f"endPosition: {endPosition}")
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
                    logging.info(f"functionString: {functionString}")
                    encodeFunctions.append(
                        "result['{0}'] = {1}".format(longName, functionString)
                    )
            except:
                logging.warning(sys.exc_info())
                pass

        encodeFunctionString = encodePositiveResponseFuncTemplate.format(
            encodePositiveResponseFunctionName, "\n    ".join(encodeFunctions)
        )
        logging.info(f"Complete encodeFunctionString: {encodeFunctionString}")
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
