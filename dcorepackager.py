import requests
import xml.etree.ElementTree as ElementTree
import tempfile
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
        'dim':'http://www.dspace.org/xmlns/dspace/dim'}

class DCOREPackager:

    def __init__(self, baseURL, handle):
        self.baseURL = baseURL.rstrip('/')
        self.handle = handle.lstrip('/').rstrip('/')

        self.baseOutDir = '/tmp/dcorepackager'

        self.oaiURL = self.baseURL+'/oai/request'
        self.headers = {'content-type': 'application/xml'}
        
        self.repositoryIdentifier = self.getOAIidentifier()
        self.identifier = 'oai'+':'+self.repositoryIdentifier+':'+self.handle

    def openTmpDir(self):
        return tempfile.TemporaryDirectory(dir=self.baseOutDir)

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

    def writeContentsFile(self, outDir):
        outFile = open(Path(outDir)/'contents', 'w')
        outFileName = outFile.name
        outFile.write('ORE.xml\tbundle:ORE')
        outFile.close()
        return outFileName

    def convertDimToDc(self, dim):
        dc_root = ElementTree.Element('dublin_core')
        dc_root.set('schema','dc')
        
        for e in dim.iter('*'):
            dc_e = ElementTree.Element('dcvalue')
            
            e_mdschema = e.get('mdschema')
            e_element = e.get('element')
            e_qualifier = e.get('qualifier')
            e_lang = e.get('lang')
            
            if (e_mdschema != 'dc'):
                continue

            if (e_element != 'none'):
                dc_e.set('element', e_element)
            else:
                raise Exception('e_element is none')

            if (e_qualifier != 'none'):
                dc_e.set('qualifier', e_qualifier)

            if (e_lang != 'none'):
                dc_e.set('language', e_lang)

            dc_e.text = e.text

            dc_root.append(dc_e)

        return ElementTree.ElementTree(dc_root)

    def writeDCxml(self, outDir):
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
        outFile = outFile = open(Path(outDir)/'dublin_core.xml', 'wb')
        outFileName = outFile.name
        dim_xml = self.convertDimToDc(xml)
        dim_xml.write(outFile)
        outFile.close()
        return outFileName

    def writeORExml(self, outDir):
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
        outFile = outFile = open(Path(outDir)/'ORE.xml', 'wb')
        outFileName = outFile.name
        xml.write(outFile)
        outFile.close()
        return outFileName
    
    def getPackage(self):
        self.writeDCxml(self.baseOutDir)
        # with self.openTmpDir() as tmpDir:
        #     pkg = ZipFile(tmpDir+'.zip', 'w')
        #     pkg.write(self.writeContentsFile(tmpDir))
        #     pkg.write(self.writeORExml(tmpDir))
        #     pkg.write(self.writeDCxml(tmpDir))
        #     pkg.close()
        #     return pkg

if __name__ == "__main__":
    baseURL = 'http://demo.dspace.org'
    handle = '10673/7'

    pack = DCOREPackager(baseURL, handle)
    pack.getPackage()