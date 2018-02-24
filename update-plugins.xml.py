# coding: utf-8
# Credits to Grégoire Piffault
# https://bitbucket.org/gpiffault/qgis-plugins/wiki/Home
# We only commented the default XSL stylesheet

from future import standard_library
standard_library.install_aliases()
import os
import configparser


def xml_lib():
    import xml.dom.minidom

    outfile = xml.dom.minidom.Document()
    # pi = outfile.createProcessingInstruction('xml-stylesheet', 'type="text/xsl" href="plugins.xsl"')
    # outfile.appendChild(pi)
    plugins = outfile.createElement('plugins')
    outfile.appendChild(plugins)

    # for dir in [name for name in os.listdir('.') if os.path.isdir(name)]:
    metadata = os.path.join('.', 'metadata.txt')
    if os.path.isfile(metadata):
        # Parse config
        config = configparser.RawConfigParser()
        config.read(metadata)
        # import ipdb; ipdb.set_trace()
        # Create xml elements
        newplugin = outfile.createElement('pyqgis_plugin')
        for attribute in ['name', 'version']:
            newplugin.setAttribute(attribute, config.get('general', attribute))
        # QGIS version
        newchild = outfile.createElement('qgis_minimum_version')
        newchild.appendChild(outfile.createTextNode(config.get('general', 'qgisMinimumVersion')))
        newplugin.appendChild(newchild)
        # Description
        newchild = outfile.createElement('description')
        newchild.appendChild(outfile.createTextNode(config.get('general', 'description')))
        newplugin.appendChild(newchild)
        # File
        newchild = outfile.createElement('file_name')
        newchild.appendChild(outfile.createTextNode(
            config.get('general', 'version') + '.zip')
        )
        newplugin.appendChild(newchild)
        # Author
        newchild = outfile.createElement('author_name')
        newchild.appendChild(outfile.createTextNode(config.get('general', 'author')))
        newplugin.appendChild(newchild)
        # download_url
        newchild = outfile.createElement('download_url')
        # newchild.appendChild(outfile.createTextNode(dir + '.zip'))
        newchild.appendChild(outfile.createTextNode('https://bitbucket.org/gpiffault/qgis-plugins/downloads/'))
        newplugin.appendChild(newchild)

        plugins.appendChild(newplugin)

    open("plugins.xml", "wb").write(outfile.toprettyxml(indent="  ", encoding="UTF-8"))


if __name__ == "__main__":
    xml_lib()
