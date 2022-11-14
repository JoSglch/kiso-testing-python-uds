import logging
from typing import Dict
from xml.etree.ElementTree import Element as XMLElement

from uds.uds_config_tool.odx.diag_coded_types import (DiagCodedType,
                                                      MinMaxLengthType,
                                                      StandardLengthType)
from uds.uds_config_tool.odx.globals import xsi


##
# param: a diag service element
# return: a dictionary with the sdgs data elements
def getSdgsData(diagServiceElement):

    output = {}

    sdgs = diagServiceElement.find("SDGS")
    sdg = sdgs.find("SDG")
    for i in sdg:
        try:
            output[i.attrib["SI"]] = i.text
        except:
            pass
    return output


##
# param: a diagServiceElement, an string representing the si attribute
# return: a specific entry from the sdgs params, or none if it does not exist
def getSdgsDataItem(diagServiceElement, itemName):

    outputDict = getSdgsData(diagServiceElement)

    try:
        output = outputDict[itemName]
    except:
        output = None

    return output


##
# param: an xml element
# return: a string with the short name, or None if no short name exists
def getShortName(xmlElement):

    try:
        output = xmlElement.find("SHORT-NAME").text
    except:
        output = None

    return output


##
# param: an xml element
# return: a string with the long name, or None if no long name exists
def getLongName(xmlElement):
    try:
        output = xmlElement.find("LONG-NAME").text
    except:
        output = None

    return output


##
# param: a diag service element, a list of other xmlElements
# return: an integer
def getServiceIdFromDiagService(diagServiceElement, xmlElements):

    requestKey = diagServiceElement.find("REQUEST-REF").attrib["ID-REF"]
    requestElement = xmlElements[requestKey]
    params = requestElement.find("PARAMS")
    for i in params:
        try:
            if i.attrib["SEMANTIC"] == "SERVICE-ID":
                return int(i.find("CODED-VALUE").text)
        except:
            pass

    return None


##
# param: a diag service element, a list of other xmlElements
# return: an integer
def getResponseIdFromDiagService(diagServiceElement, xmlElements):

    requestKey = diagServiceElement.find("REQUEST-REF").attrib["ID-REF"]
    requestElement = xmlElements[requestKey]
    params = requestElement.find("PARAMS")
    for i in params:
        try:
            if i.attrib["SEMANTIC"] == "SERVICE-ID":
                return int(i.find("CODED-VALUE").text)
        except:
            pass

    return None


##
# params: an xmlElement, the name of a semantic to match
# return: a single parameter matching the semantic, or a list of parameters which match the semantic
def getParamWithSemantic(xmlElement, semanticName):

    output = None

    try:
        params = xmlElement.find("PARAMS")
    except AttributeError:
        return output

    paramsList = []

    for i in params:
        paramSemantic = i.attrib["SEMANTIC"]
        if paramSemantic == semanticName:
            paramsList.append(i)

    if len(paramsList) == 0:
        output = None
    elif len(paramsList) == 1:
        output = paramsList[0]
    else:
        output = paramsList
    return output


##
# params: a diagnostic service element xml entry, and the dictionary of all possible xml elements
# return: if only 1 element, then a single xml element, else a list of xml elements, or none if no positive responses
def getPositiveResponse(diagServiceElement, xmlElements):

    positiveResponseList = []
    try:
        positiveResponseReferences = diagServiceElement.find("POS-RESPONSE-REFS")
    except:
        return None

    if positiveResponseReferences is None:
        return None
    else:
        for i in positiveResponseReferences:
            try:
                positiveResponseList.append(xmlElements[i.attrib["ID-REF"]])
            except:
                pass

    positiveResponseList_length = len(positiveResponseList)
    if positiveResponseList_length == 0:
        return None
    if positiveResponseList_length:
        return positiveResponseList[0]
    else:
        return positiveResponseList


def getDiagObjectProp(paramElement, xmlElements):

    try:
        dopElement = xmlElements[paramElement.find("DOP-REF").attrib["ID-REF"]]
    except:
        dopElement = None

    return dopElement


def getBitLengthFromDop(diagObjectPropElement: XMLElement):

    try:
        bitLength = int(
            diagObjectPropElement.find("DIAG-CODED-TYPE").find("BIT-LENGTH").text
        )
    except:
        bitLength = None

    return bitLength


def isDiagServiceTransmissionOnly(diagServiceElement):

    output = getSdgsDataItem(diagServiceElement, "PositiveResponseSuppressed")

    if output is not None:
        if output == "yes":
            return True

    return False


def findDescendant(name: str, root: XMLElement) -> XMLElement:
    """Search for an element in all descendants of an element by tag name, returns first instance
    """
    logging.debug(f"\nSearch {name} in {root} ({(root.find('SHORT-NAME')).text})")
    for child in root.iter():
        if child.tag == name:
            logging.debug(f"Found child: {child}")
            logging.debug(f"Reference ID is: {child.attrib['ID-REF']}")
            return child
    return None


def getDiagCodedTypeFromDop(dataObjectProp: XMLElement) -> DiagCodedType:
    """Parse ODX to get the DIAG CODED TYPE from a DATA OBJECT PROP and create
    DiagCodedType object containing necessary info to calculate the length of the response
    and decode it
    """
    logging.debug("DATA OBJECT PROP")
    diagCodedTypeElement = dataObjectProp.find("DIAG-CODED-TYPE")
    lengthType = diagCodedTypeElement.get(f"{xsi}type")
    base_data_type = diagCodedTypeElement.attrib["BASE-DATA-TYPE"]
    if lengthType == "STANDARD-LENGTH-TYPE":
        logging.debug("Standard Length DOP")
        bitLengthElement = diagCodedTypeElement.find("BIT-LENGTH")
        bitLength = int(bitLengthElement.text)
        # TODO: do this in DiagCodedType instead
        byteLength = int(bitLength / 8)
        logging.debug(f"bitLength: {bitLength}, byteLength: {byteLength}")
        diagCodedType = StandardLengthType(base_data_type, byteLength)
        logging.debug(f"Created diagCodedType: {diagCodedType}")
    elif lengthType == "MIN-MAX-LENGTH-TYPE":
        logging.debug("Min Max Length DOP")
        minLengthElement = diagCodedTypeElement.find("MIN-LENGTH")
        maxLengthElement = diagCodedTypeElement.find("MAX-LENGTH")
        minLength = None
        maxLength = None
        if minLengthElement is not None:
            minLength = int(minLengthElement.text)
        if maxLengthElement is not None:
            maxLength = int(maxLengthElement.text)
        termination = diagCodedTypeElement.attrib["TERMINATION"]
        diagCodedType = MinMaxLengthType(base_data_type, minLength, maxLength, termination)
        logging.debug(f"Created diagCodedType: {diagCodedType}")
    else:
        raise NotImplementedError(f"Handling of {lengthType} is not implemented")
    return diagCodedType


def getDiagCodedTypeFromStructure(structure: XMLElement, xmlElements: Dict[str, XMLElement]) -> DiagCodedType:
    """Parse ODX to get the DIAG CODED TYPE from a STRUCTURE and create
    DiagCodedType object containing necessary info to calculate the length of the response
    and decode it
    """
    byteSizeElement = structure.find("BYTE-SIZE")
    # STRUCTURE with BYTE-SIZE
    if structure.find("BYTE-SIZE") is not None:
        logging.debug("Static Length Structure...")
        byteLength = int(byteSizeElement.text)
        # get decoding info from first DOP, assume same decoding for each param
        dop = xmlElements[
            findDescendant("DOP-REF", structure).attrib["ID-REF"]
        ]
        base_data_type = dop.find("DIAG-CODED-TYPE").attrib["BASE-DATA-TYPE"]
        logging.debug(f"base data type: {base_data_type}")
        diagCodedType = StandardLengthType(base_data_type, byteLength)
        logging.debug(f"Created diagCodedType: {diagCodedType}")
    # STRUCTURE with DOP-REF
    else:
        logging.debug("Could not get BYTE-SIZE from STRUCTURE, checking for DOP-REF")
        dopRef = findDescendant("DOP-REF", structure)
        if dopRef is None:
            raise AttributeError("Could not find DOP from Structure, and no BYTE-SIZE: ODX probably invalid")
        nestedDop = xmlElements[dopRef.attrib["ID-REF"]]
        logging.debug(f"dopRef= {dopRef}, dop= {nestedDop}")
        logging.debug("Nested DOP from STRUCTURE:")
        if nestedDop.tag == "DATA-OBJECT-PROP":
            diagCodedType = getDiagCodedTypeFromDop(nestedDop)
        elif nestedDop.tag == "END-OF-PDU-FIELD":
            # TODO: handle END-OF-PDU-FIELD?
            logging.debug("Found END-OF-PDU-FIELD")
        else:
            # nested structure (if possible in ODX spec):
            # recursively check structure: return getDiagCodedTypeFromStructure(nestedDop, xmlElements)
            raise NotImplementedError(f"parsing of {nestedDop.tag} is not implemented")
    return diagCodedType


if __name__ == "__main__":

    pass
