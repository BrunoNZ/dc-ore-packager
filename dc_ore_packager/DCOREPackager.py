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
        verifySSL=True, idExceptions={}, outDir=None, outFile=None):

        self.baseURL = baseURL.rstrip('/')

        # OAI identifier exceptions
        self.idExceptions = idExceptions

        # Verify SSL flag:
        self.verifySSL = verifySSL

        self.oaiURL = self.baseURL+'/oai/request'
        self.headers = {'content-type': 'application/xml'}

        self.repositoryIdentifier = self.getOAIidentifier()
        self.oaiIdentifierString = 'oai' + ':' + self.repositoryIdentifier + ':'

        # Item Number. Used to create directories into ZipFile
        self.nItems = len(handleList)

        # List of Handles and Identifiers
        self.handle = []
        self.identifier = []
        for h in handleList:
            handle = h.lstrip('/').rstrip('/')
            self.handle.append(handle)
            self.identifier.append(self.oaiIdentifierString + handle)

        # Register Namespaces in ElementTree
        for prefix, uri in self.NAMESPACES.items():
            ElementTree.register_namespace(prefix, uri)

        # Define outDir for getTempFile method
        self.outDir = outDir
        if (self.outDir is None):
            self.outDir = './tmp'

        # Define outZip for getPackage method
        self.outFile = outFile
        if (self.outFile is None):
            self.outFile = self.getTempFile()

        # Debug option: Allow not delete file at end of execution
        self.deleteOutfile = False


    def __del__(self):
        if self.deleteOutfile & os.path.exists(self.outFile):
            os.remove(self.outFile)


    def getTempFile(self):
        return Path(self.outDir+'/'+str(uuid.uuid4())+'.zip')


    def getOAIidentifierException(self):
        return self.idExceptions.get(self.baseURL)


    def getOAIRequest(self,options):
        return requests.get(self.oaiURL, options,
                            headers=self.headers, verify=self.verifySSL)


    def getOAIidentifier(self):

        # Verify if there is an exception for self.baseURL
        idException = self.getOAIidentifierException()
        if idException is not None:
            return idException

        options = {
            'verb': 'Identify'
        }
        r = self.getOAIRequest(options)
        xml = ElementTree.fromstring(r.content)\
                .find('oai:Identify', namespaces=self.NAMESPACES)\
                .find('oai:description', namespaces=self.NAMESPACES)\
                .find('oai_id:oai-identifier', namespaces=self.NAMESPACES)\
                .find('oai_id:repositoryIdentifier', namespaces=self.NAMESPACES)
        return xml.text


    def writeContentsFile(self, outFile):
        outFile.write(b'ORE.xml\tbundle:ORE')
        pass


    def convertDimToDc(self, dim):
        dc_root = ElementTree.Element('dublin_core')
        dc_root.set('schema','dc')

        for e in dim.iter('*'):
            dc_e = ElementTree.SubElement(dc_root,'dcvalue')

            e_mdschema = e.get('mdschema')
            e_element = e.get('element')
            e_qualifier = e.get('qualifier')
            e_lang = e.get('lang')

            if (e_mdschema != 'dc'):
                continue

            if (e_element is not None):
                dc_e.set('element', e_element)
            else:
                raise Exception('e_element is none')

            if (e_qualifier is not None):
                dc_e.set('qualifier', e_qualifier)

            if (e_lang is not None):
                dc_e.set('language', e_lang)

            dc_e.text = e.text

        return ElementTree.ElementTree(dc_root)


    def writeDCxml(self, outFile, identifier):
        options = {
            'verb': 'GetRecord',
            'metadataPrefix': 'dim',
            'identifier': identifier
        }
        r = self.getOAIRequest(options)
        xml = ElementTree.ElementTree(\
                ElementTree.fromstring(r.content)\
                .find('oai:GetRecord', namespaces=self.NAMESPACES)\
                .find('oai:record', namespaces=self.NAMESPACES)\
                .find('oai:metadata', namespaces=self.NAMESPACES)
                .find('dim:dim', namespaces=self.NAMESPACES)\
            )
        dim_xml = self.convertDimToDc(xml)
        dim_xml.write(outFile, xml_declaration=True, encoding='utf-8')
        pass


    def writeORExml(self, outFile, identifier):
        options = {
            'verb': 'GetRecord',
            'metadataPrefix': 'ore',
            'identifier': identifier
        }
        r = self.getOAIRequest(options)
        xml = ElementTree.ElementTree(\
                ElementTree.fromstring(r.content)\
                    .find('oai:GetRecord', namespaces=self.NAMESPACES)\
                    .find('oai:record', namespaces=self.NAMESPACES)\
                    .find('oai:metadata', namespaces=self.NAMESPACES)\
                    .find('atom:entry', namespaces=self.NAMESPACES)\
                )
        xml.write(outFile, encoding='utf-8')
        pass


    def getPackage(self):
        try:
            with ZipFile(self.outFile, 'w') as outZip:
                for item in range(0,self.nItems):
                    dID = str(item+1)
                    with outZip.open(dID + '/dublin_core.xml', 'w') as outFile:
                        self.writeDCxml(outFile, self.identifier[item])

                    with outZip.open(dID + '/ORE.xml', 'w') as outFile:
                        self.writeORExml(outFile, self.identifier[item])

                    with outZip.open(dID + '/contents', 'w') as outFile:
                        self.writeContentsFile(outFile)

        except AttributeError as e:
            return
            raise

        else:
            return self.outFile
