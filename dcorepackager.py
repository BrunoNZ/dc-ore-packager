import requests
import xml.etree.ElementTree as ElementTree
import uuid
import os
import sys
from pathlib import Path
from zipfile import ZipFile

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

class DCOREPackager:
    
    def __init__(self, baseURL, handle, outDir=None, outFile=None):
        self.baseURL = baseURL.rstrip('/')
        self.handle = handle.lstrip('/').rstrip('/')

        self.oaiURL = self.baseURL+'/oai/request'
        self.headers = {'content-type': 'application/xml'}
        
        self.repositoryIdentifier = self.getOAIidentifier()
        self.identifier = 'oai'+':'+self.repositoryIdentifier+':'+self.handle

        # Register Namespaces in ElementTree
        for prefix, uri in NAMESPACES.items():
            ElementTree.register_namespace(prefix, uri)

        # Define outDir for getTempFile method
        self.outDir = outDir
        if (self.outDir is None):
            self.outDir = './tmp'

        # Define outZip for getPackage method
        self.outFile = outFile
        if (self.outFile is None):
            self.outFile = self.getTempFile()

    def __del__(self):
        if os.path.exists(self.outFile):
            os.remove(self.outFile)

    def getTempFile(self):
        return Path(self.outDir+'/'+str(uuid.uuid4())+'.zip')

    def getOAIidentifier(self):
        options = {
            'verb': 'Identify'
        }
        r = requests.get(self.oaiURL, options, headers=self.headers)
        xml = ElementTree.fromstring(r.content)\
                .find('oai:Identify', namespaces=NAMESPACES)\
                .find('oai:description', namespaces=NAMESPACES)\
                .find('oai_id:oai-identifier', namespaces=NAMESPACES)\
                .find('oai_id:repositoryIdentifier', namespaces=NAMESPACES)
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

    def writeDCxml(self, outFile):
        options = {
            'verb': 'GetRecord',
            'metadataPrefix': 'dim',
            'identifier': self.identifier
        }
        r = requests.get(self.oaiURL, options, headers=self.headers)
        xml = ElementTree.ElementTree(\
                ElementTree.fromstring(r.content)\
                    .find('oai:GetRecord', namespaces=NAMESPACES)\
                    .find('oai:record', namespaces=NAMESPACES)\
                    .find('oai:metadata', namespaces=NAMESPACES)
                    .find('dim:dim', namespaces=NAMESPACES)\
                )
        dim_xml = self.convertDimToDc(xml)
        dim_xml.write(outFile, xml_declaration=True, encoding='utf-8')
        pass

    def writeORExml(self, outFile):
        options = {
            'verb': 'GetRecord',
            'metadataPrefix': 'ore',
            'identifier': self.identifier
        }
        r = requests.get(self.oaiURL, options, headers=self.headers)
        xml = ElementTree.ElementTree(\
                ElementTree.fromstring(r.content)\
                    .find('oai:GetRecord', namespaces=NAMESPACES)\
                    .find('oai:record', namespaces=NAMESPACES)\
                    .find('oai:metadata', namespaces=NAMESPACES)\
                    .find('atom:entry', namespaces=NAMESPACES)\
                )
        xml.write(outFile, encoding='utf-8')
        pass

    def getPackage(self):
        with ZipFile(self.outFile, 'w') as outZip:
            with outZip.open('dublin_core.xml', 'w') as outFile:
                self.writeDCxml(outFile)
            
            with outZip.open('ORE.xml', 'w') as outFile:
                self.writeORExml(outFile)

            with outZip.open('contents', 'w') as outFile:
                self.writeContentsFile(outFile)
        
        return self.outFile

if __name__ == "__main__":
    baseURL = 'http://demo.dspace.org'
    handle = '10673/7'

    pack = DCOREPackager(baseURL, handle)
    f = pack.getPackage()
    print(f)