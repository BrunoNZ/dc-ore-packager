# dc-ore-packager

A tool to create a [SimpleArchivePackage](https://wiki.duraspace.org/display/DSDOC6x/Importing+and+Exporting+Items+via+Simple+Archive+Format#ImportingandExportingItemsviaSimpleArchiveFormat-DSpaceSimpleArchiveFormat) package from a BaseURL and a Handle of an item of any repository that supports OAI protocol, which can be imported by [DSpace's Batch Import](https://wiki.duraspace.org/display/DSDOC6x/Importing+and+Exporting+Items+via+Simple+Archive+Format#ImportingandExportingItemsviaSimpleArchiveFormat-UIBatchImport(XMLUI)) tool.

The objective is to create a clone of the given item using a link to its bitstreams and a copy of its bitstreams. The link is made using [ORE format](https://wiki.duraspace.org/display/DSDOC6x/OAI+2.0+Server#OAI2.0Server-MetadataFormats), so that the bitstreams are shown in the graphical interface in the exactly same way as the original item.

To use it:
```python
from dc_ore_packager import DCOREPackager
repositoryURL = 'http://demo.dspace.org'
handleList = ['10673/3','10673/4','10673/5','10673/6','10673/7']
i = DCOREPackager(repositoryURL, handleList, outDir='/tmp')
print(i.getPackage())
```

A sample WebApp that receives a URL and send a package file: [dc-ore-packager-webapp](https://github.com/BrunoNZ/dc-ore-packager-webapp)
