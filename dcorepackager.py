import requests
import xml.etree.ElementTree as ElementTree
import tempfile
from pathlib import Path
from zipfile import ZipFile

class DCOREPackager:

    def __init__(self, baseURL, handle):
        self.baseURL = baseURL.rstrip('/')
        self.handle = handle.lstrip('/').rstrip('/')

        self.baseOutDir = None
        self.handleName = self.handle.replace('/','-')+'_'

        self.oaiURL = self.baseURL+'/oai/request'
        self.headers = {'content-type': 'application/xml'}
        self.namespaces = {
            'oai':'http://www.openarchives.org/OAI/2.0/',
            'oai_dc':'http://www.openarchives.org/OAI/2.0/oai_dc/',
            'atom':'http://www.w3.org/2005/Atom',
            'oai_id':'http://www.openarchives.org/OAI/2.0/oai-identifier',
            'qdc':'http://dspace.org/qualifieddc/',
            'xoai':'http://www.lyncode.com/xoai',
            'dcterms':'http://purl.org/dc/terms/'}
        
        self.repositoryIdentifier = self.getOAIidentifier()
        self.identifier = 'oai'+':'+self.repositoryIdentifier+':'+self.handle

    def openTmpDir(self):
        return tempfile.TemporaryDirectory(
                    prefix=self.handleName,
                    dir=self.baseOutDir)

    def getOAIidentifier(self):
        options = {
            'verb': 'Identify'
        }
        r = requests.get(self.oaiURL, options, headers=self.headers)
        xml = ElementTree.fromstring(r.content)\
                .find('oai:Identify', namespaces=self.namespaces)\
                .find('oai:description', namespaces=self.namespaces)\
                .find('oai_id:oai-identifier', namespaces=self.namespaces)\
                .find('oai_id:repositoryIdentifier', namespaces=self.namespaces)
        return xml.text

    def writeContentsFile(self, outDir):
        outFile = open(Path(outDir)/'contents', 'w')
        outFileName = outFile.name
        outFile.write('ORE.xml\tbundle:ORE')
        outFile.close()
        return outFileName

    def writeDCxml(self, outDir):
        options = {
            'verb': 'GetRecord',
            'metadataPrefix': 'qdc',
            'identifier': self.identifier
        }
        r = requests.get(self.oaiURL, options, headers=self.headers)
        xml = ElementTree.ElementTree(\
                ElementTree.fromstring(r.content)\
                    .find('oai:GetRecord', namespaces=self.namespaces)\
                    .find('oai:record', namespaces=self.namespaces)\
                    .find('oai:metadata', namespaces=self.namespaces)
                    .find('qdc:qualifieddc', namespaces=self.namespaces)\
                )
        outFile = outFile = open(Path(outDir)/'dublin_core.xml', 'wb')
        outFileName = outFile.name
        xml.write(outFile)
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
                    .find('oai:GetRecord', namespaces=self.namespaces)\
                    .find('oai:record', namespaces=self.namespaces)\
                    .find('oai:metadata', namespaces=self.namespaces)\
                    .find('atom:entry', namespaces=self.namespaces)\
                )
        outFile = outFile = open(Path(outDir)/'ORE.xml', 'wb')
        outFileName = outFile.name
        xml.write(outFile)
        outFile.close()
        return outFileName
    
    def getPackage(self):
        with self.openTmpDir() as tmpDir:
            pkg = ZipFile(tmpDir+'.zip', 'w')
            pkg.write(self.writeContentsFile(tmpDir))
            pkg.write(self.writeORExml(tmpDir))
            pkg.write(self.writeDCxml(tmpDir))
            pkg.close()
            return pkg

if __name__ == "__main__":
    baseURL = 'http://demo.dspace.org'
    handle = '10673/7'

    pack = DCOREPackager(baseURL, handle)
    pack.getPackage()