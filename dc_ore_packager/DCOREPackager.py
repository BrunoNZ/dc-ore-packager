import requests
import xml.etree.ElementTree as ElementTree
import uuid
import os
from pathlib import Path
from zipfile import ZipFile

class DCOREPackager:

    NAMESPACES = {
            'oai':'http://www.openarchives.org/OAI/2.0/',
            'oai_dc':'http://www.openarchives.org/OAI/2.0/oai_dc/',
            'atom':'http://www.w3.org/2005/Atom',
            'oai_id':'http://www.openarchives.org/OAI/2.0/oai-identifier',
            'qdc':'http://dspace.org/qualifieddc/',
            'xoai':'http://www.lyncode.com/xoai',
            'dcterms':'http://purl.org/dc/terms/',
            'dim':'http://www.dspace.org/xmlns/dspace/dim',
            'oreatom':'http://www.openarchives.org/ore/atom/'}


    def __init__(
        self, baseURL, handleList,
        verifySSL=True,
        idExceptions={},
        outDir=None,
        outFile=None,
        useIdPrefix=False,
        deleteOutfile=False,
        debug=False):

        # Debug options: Allow not delete file at end of execution
        self.deleteOutfile = deleteOutfile
        self.debug = debug

        # Base URL
        self.baseURL = baseURL.rstrip('/')

        # OAI identifier exceptions
        self.idExceptions = idExceptions
        self.useIdPrefix = useIdPrefix

        # Verify SSL flag:
        self.verifySSL = verifySSL

        self.oaiURL = self.baseURL+'/oai/request'
        self.headers = {'content-type': 'application/xml'}

        # Verify SSL flag:
        self.verifySSL = verifySSL

        # Register Namespaces in ElementTree
        for prefix, uri in self.NAMESPACES.items():
            ElementTree.register_namespace(prefix, uri)

        # Get OAI Repository Identifier
        self.repositoryIdentifier = self.getOAIidentifier()
        delim = self.repositoryIdentifier['delimiter']
        self.oaiIdentifierString = 'oai' + delim + self.repositoryIdentifier['id'] + delim

        # Item Number. Used to create directories into ZipFile
        self.nItems = len(handleList)

        # List of Handles and Identifiers
        self.handle = []
        self.identifier = []
        for h in handleList:
            handle = self.prepareHandle(h)
            self.handle.append(handle)
            self.identifier.append(self.oaiIdentifierString + handle)

        # Define outDir for getTempFile method
        self.outDir = outDir
        if (self.outDir is None):
            self.outDir = './tmp'

        # Define outZip for getPackage method
        self.outFile = outFile
        if (self.outFile is None):
            self.outFile = self.getTempFile()

        self.dcSet = set()

        if (self.debug):
            self.printDebug()


    def __del__(self):
        if self.deleteOutfile & os.path.exists(self.outFile):
            os.remove(self.outFile)


    def getTempFile(self):
        return Path(self.outDir+'/'+str(uuid.uuid4())+'.zip')


    def getIdentifierException(self, exceptType):
        e = self.idExceptions.get(self.baseURL)
        return e.get(exceptType) if e is not None else None


    def getOAIRequest(self,options):
        return requests.get(self.oaiURL, options,
                            headers=self.headers, verify=self.verifySSL)


    def getOAIidentifier(self):

        oai_id = {}
        
        options = {
            'verb': 'Identify'
        }

        # Verify if there is an exception for self.baseURL
        idException = self.getIdentifierException("id")
        if idException is not None:
            oai_id['id'] = idException
            oai_id['delimiter'] = ':'
            oai_id['sample'] = None
            oai_id['handlePrefix'] = None

        else:
            r = self.getOAIRequest(options)
            xml = ElementTree.fromstring(r.content)\
                    .find('oai:Identify', namespaces=self.NAMESPACES)\
                    .find('oai:description', namespaces=self.NAMESPACES)\
                    .find('oai_id:oai-identifier', namespaces=self.NAMESPACES)

            oai_id['id'] = xml.find('oai_id:repositoryIdentifier', namespaces=self.NAMESPACES).text
            oai_id['delimiter'] = xml.find('oai_id:delimiter', namespaces=self.NAMESPACES).text
            oai_id['sample'] = xml.find('oai_id:sampleIdentifier', namespaces=self.NAMESPACES).text
            oai_id['handlePrefix'] = oai_id['sample'].split(oai_id['delimiter'])[-1].split('/')[0]

        if (self.debug):
            print(r.content)
            print(oai_id)

        return oai_id


    def prepareHandle(self, handle):
        handle = handle.lstrip('/').rstrip('/')
        useIdPrefix = self.useIdPrefix or (self.getIdentifierException("useIdPrefix") is not None)
        if useIdPrefix & (self.repositoryIdentifier['handlePrefix'] is not None):
            handle = self.repositoryIdentifier['handlePrefix'] + '/' + handle.split('/')[-1]
        return handle


    def convertDimToDc(self, dim):
        dc_root = ElementTree.Element('dublin_core')
        dc_root.set('schema','dc')
        dc_list = []

        for e in dim.iter('*'):
            dc_e = ElementTree.SubElement(dc_root,'dcvalue')

            e_mdschema = e.get('mdschema')
            e_element = e.get('element')
            e_qualifier = e.get('qualifier')
            e_lang = e.get('lang')

            md = "dc"

            if (e_mdschema != 'dc'):
                continue

            if (e_element is not None):
                dc_e.set('element', e_element)
                md += "." + e_element
            else:
                raise Exception('e_element is none')

            if (e_qualifier is not None):
                dc_e.set('qualifier', e_qualifier)
                md += "." + e_qualifier

            if (e_lang is not None):
                dc_e.set('language', e_lang)

            dc_e.text = e.text

            dc_list.append(md)

        return ElementTree.ElementTree(dc_root), dc_list


    def getDIMxml(self, identifier):
        options = {
            'verb': 'GetRecord',
            'metadataPrefix': 'dim',
            'identifier': identifier
        }
        r = self.getOAIRequest(options)
        return ElementTree.ElementTree(\
                ElementTree.fromstring(r.content)\
                    .find('oai:GetRecord', namespaces=self.NAMESPACES)\
                    .find('oai:record', namespaces=self.NAMESPACES)\
                    .find('oai:metadata', namespaces=self.NAMESPACES)
                    .find('dim:dim', namespaces=self.NAMESPACES)
                )


    def getORExml(self, identifier):
        options = {
            'verb': 'GetRecord',
            'metadataPrefix': 'ore',
            'identifier': identifier
        }
        r = self.getOAIRequest(options)
        return ElementTree.ElementTree(\
                ElementTree.fromstring(r.content)\
                    .find('oai:GetRecord', namespaces=self.NAMESPACES)\
                    .find('oai:record', namespaces=self.NAMESPACES)\
                    .find('oai:metadata', namespaces=self.NAMESPACES)\
                    .find('atom:entry', namespaces=self.NAMESPACES)
                )
        
        
    def writeContentsFile(self, outFile):
        outFile.write(b'ORE.xml\tbundle:ORE')
        pass


    def getPackage(self):
        try:
            with ZipFile(self.outFile, 'w') as outZip:
                for item in range(0,self.nItems):
                    dc_xml, dc_list = self.convertDimToDc(self.getDIMxml(self.identifier[item]))
                    ore_xml = self.getORExml(self.identifier[item])
                    dID = str(item+1)
                    with outZip.open(dID + '/dublin_core.xml', 'w') as outFile:
                        dc_xml.write(outFile, xml_declaration=True, encoding='utf-8')

                    with outZip.open(dID + '/ORE.xml', 'w') as outFile:
                        ore_xml.write(outFile, encoding='utf-8')

                    with outZip.open(dID + '/contents', 'w') as outFile:
                        self.writeContentsFile(outFile)

                    self.dcSet.update(dc_list)

        except AttributeError as e:
            raise e

        else:
            return self.outFile

    
    def getDCElements(self):
        return self.dcSet


    def printDebug(self):
        print("* self.baseURL", self.baseURL, sep=": ")
        print("* self.idExceptions", self.idExceptions, sep=": ")
        print("* self.useIdPrefix", self.useIdPrefix, sep=": ")
        print("* self.verifySSL", self.verifySSL, sep=": ")
        print("* self.oaiURL", self.oaiURL, sep=": ")
        print("* self.headers", self.headers, sep=": ")
        print("* self.verifySSL", self.verifySSL, sep=": ")
        print("* self.repositoryIdentifier", self.repositoryIdentifier, sep=": ")
        print("* self.oaiIdentifierString", self.oaiIdentifierString, sep=": ")
        print("* self.nItems", self.nItems, sep=": ")
        print("* self.handle", self.handle, sep=": ")
        print("* self.identifier", self.identifier, sep=": ")
        print("* self.outDir", self.outDir, sep=": ")
        print("* self.outFile", self.outFile, sep=": ")
        print("* self.deleteOutfile", self.deleteOutfile, sep=": ")
        print("* self.debug", self.debug, sep=": ")
