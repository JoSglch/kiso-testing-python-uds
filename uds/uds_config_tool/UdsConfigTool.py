#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"


import xml.etree.ElementTree as ET

from uds.uds_communications.Uds.Uds import Uds
from uds.uds_config_tool.SupportedServices.ReadDataByIdentifierContainer import ReadDataByIdentifierContainer
from uds.uds_config_tool.FunctionCreation.ReadDataByIdentifierMethodFactory import ReadDataByIdentifierMethodFactory
from uds.uds_config_tool.SupportedServices.WriteDataByIdentifierContainer import WriteDataByIdentifierContainer
from uds.uds_config_tool.FunctionCreation.WriteDataByIdentifierMethodFactory import WriteDataByIdentifierMethodFactory
from uds.uds_config_tool.SupportedServices.ECUResetContainer import ECUResetContainer
from uds.uds_config_tool.FunctionCreation.ECUResetMethodFactory import ECUResetMethodFactory

supportedServices = {22, }  # ?????????????? what's this used for? Doesn't appear to have a purposeat present - should be [0x22, 0x2E] ?

def get_serviceIdFromXmlElement(diagServiceElement, xmlElements):

    requestKey = diagServiceElement.find('REQUEST-REF').attrib['ID-REF']
    requestElement = xmlElements[requestKey]
    params = requestElement.find('PARAMS')
    for i in params:
        try:
            if(i.attrib['SEMANTIC'] == 'SERVICE-ID'):
                return int(i.find('CODED-VALUE').text)
        except:
            pass

    return None


def fill_dictionary(xmlElement):
    temp_dictionary = {}
    for i in xmlElement:
        temp_dictionary[i.attrib['ID']] = i

    return temp_dictionary


def createUdsConnection(xmlFile, ecuName):

    root = ET.parse(xmlFile)

    # create any supported containers
    rdbiContainer = ReadDataByIdentifierContainer()
    wdbiContainer = WriteDataByIdentifierContainer()
    ecuResetContainer = ECUResetContainer()
    sessionService_flag = False
    ecuResetService_flag = False
    rdbiService_flag = False
    wdbiService_flag = False
    xmlElements = {}

    for child in root.iter():
        currTag = child.tag
        try:
            xmlElements[child.attrib['ID']] = child
        except KeyError:
            pass

    for key, value in xmlElements.items():
        if value.tag == 'DIAG-SERVICE':
            serviceId = get_serviceIdFromXmlElement(value, xmlElements)
            sdg = value.find('SDGS').find('SDG')
            humanName = ""
            for sd in sdg:
                try:
                    if sd.attrib['SI'] == 'DiagInstanceName':
                        humanName = sd.text
                except KeyError:
                    pass

            if serviceId == 0x10:
                sessionService_flag = True
                pass
            elif serviceId == 0x11:
                ecuResetService_flag = True
				
                requestFunc = ECUResetMethodFactory.create_requestFunction(value, xmlElements)
                ecuResetContainer.add_requestFunction(requestFunc, humanName)

                negativeResponseFunction = ECUResetMethodFactory.create_checkNegativeResponseFunction(value, xmlElements)
                ecuResetContainer.add_negativeResponseFunction(negativeResponseFunction, humanName)

                checkFunc = ECUResetMethodFactory.create_checkPositiveResponseFunction(value, xmlElements)
                ecuResetContainer.add_checkFunction(checkFunc, humanName)

                positiveResponseFunction = ECUResetMethodFactory.create_encodePositiveResponseFunction(value, xmlElements)
                ecuResetContainer.add_positiveResponseFunction(positiveResponseFunction, humanName)
            elif serviceId == 0x22:
                rdbiService_flag = True

                # The new code extends the range of functions required, in order to handle RDBI working for concatenated lists of DIDs ...
                requestFunctions = ReadDataByIdentifierMethodFactory.create_requestFunctions(value, xmlElements)
                rdbiContainer.add_requestSIDFunction(requestFunctions[0], humanName)  # ... note: this will now need to handle replication of this one!!!!
                rdbiContainer.add_requestDIDFunction(requestFunctions[1], humanName)


                negativeResponseFunction = ReadDataByIdentifierMethodFactory.create_checkNegativeResponseFunction(value, xmlElements)
                rdbiContainer.add_negativeResponseFunction(negativeResponseFunction, humanName)


                checkFunctions = ReadDataByIdentifierMethodFactory.create_checkPositiveResponseFunctions(value, xmlElements)
                rdbiContainer.add_checkSIDResponseFunction(checkFunctions[0], humanName)
                rdbiContainer.add_checkSIDLengthFunction(checkFunctions[1], humanName)
                rdbiContainer.add_checkDIDResponseFunction(checkFunctions[2], humanName)
                rdbiContainer.add_checkDIDLengthFunction(checkFunctions[3], humanName)


                positiveResponseFunction = ReadDataByIdentifierMethodFactory.create_encodePositiveResponseFunction(value, xmlElements)
                rdbiContainer.add_positiveResponseFunction(positiveResponseFunction, humanName)
            elif serviceId == 0x27:
                pass

            elif serviceId == 0x2E:

                wdbiService_flag = True
                requestFunc = WriteDataByIdentifierMethodFactory.create_requestFunction(value, xmlElements)
                wdbiContainer.add_requestFunction(requestFunc, humanName)

                negativeResponseFunction = WriteDataByIdentifierMethodFactory.create_checkNegativeResponseFunction(value, xmlElements)
                wdbiContainer.add_negativeResponseFunction(negativeResponseFunction, humanName)

                checkFunc = WriteDataByIdentifierMethodFactory.create_checkPositiveResponseFunction(value, xmlElements)
                wdbiContainer.add_checkFunction(checkFunc, humanName)

                positiveResponseFunction = WriteDataByIdentifierMethodFactory.create_encodePositiveResponseFunction(value, xmlElements)
                wdbiContainer.add_positiveResponseFunction(positiveResponseFunction, humanName)
            elif serviceId == 0x2F:
                pass

    #need to be able to extract the reqId and resId
    outputEcu = Uds(reqId=0x600, resId=0x650)

    # Bind any rdbi services have been found
    if rdbiService_flag:
        setattr(outputEcu, 'readDataByIdentifierContainer', rdbiContainer)
        rdbiContainer.bind_function(outputEcu)

    # Bind any wdbi services have been found
    if wdbiService_flag:
        setattr(outputEcu, 'writeDataByIdentifierContainer', wdbiContainer)
        wdbiContainer.bind_function(outputEcu)
		
    # Bind any ECU Reset services have been found
    if ecuResetService_flag:
        setattr(outputEcu, 'ecuResetContainer', ecuResetContainer)
        ecuResetContainer.bind_function(outputEcu)

    return outputEcu


if __name__ == "__main__":

    a = createUdsConnection('Bootloader.odx', 'bootloader')

    a.readDataByIdentifier('ECU Serial Number')
    a.writeDataByIdentifier('ECU Serial Number','ABC0011223344556')
    a.ecuReset('Hard Reset',suppressResponse=False)
