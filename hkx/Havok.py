import bpy
import os
import subprocess
import xml.etree.cElementTree as et
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator
from typing import List
import re

class HKX:
    hkx_collection = None
    hkRootLevelContainer = None
    dataroot = None

    
    def readHKClass(self, element : et.Element, collection=None):
        # This tree sucks 
        if (element.attrib["class"] == "hkRootLevelContainer"):
            
            namedVars = element.find("hkparam[@name='namedVariants']")
            hkobject = namedVars.find("hkobject")
            nameparam = hkobject.find("hkparam[@name='name']")
            if nameparam != None:
                if (nameparam.text == "Scene Data"):
                    variant = hkobject.find("hkparam[@name='variant']")
                    self.getHKClassByVariant(variant.text)
                        
        if (element.attrib["class"] == "hkxScene"):
            print("HKX Scene found!")
            self.getHKClassByVariant(element.find("hkparam[@name='rootNode']").text, self.hkRootLevelContainer)
        
        if (element.attrib["class"] == "hkxNode"):
            if collection == None:
                collection = self.hkx_collection
            
            collection2 = bpy.data.collections.new(element.find("hkparam[@name='name']").text)
            children_element = element.find("hkparam[@name='children']")
            if children_element is not None and children_element.text is not None:
                children_text = children_element.text.strip()
                children = re.findall(r"#\d+", children_text)
                for child in children:
                    self.getHKClassByVariant(child, collection2)
            
            collection.children.link(collection2)
                    
                        
            
            
    
    def getHKClassByVariant(self, id, collection=None):
        node = self.dataroot.find("hkobject[@name='" + id + "']") 
        self.readHKClass(node, collection)
    


    def load(self, filepath):
        self.hkx_collection = bpy.data.collections.new("HKX")

        print("--------------------------------------")
        print("HAVOK LOADER BY GAMING WITH PORTALS")
        print("--------------------------------------")
        print("Designed for Metal Gear Rising: Revengeance (2013)")
        print("Loading Havok File")
        sxml = open(filepath, "rt").read()
        tree=et.fromstring(sxml)
        
        self.dataroot = tree.find(".//hksection[@name='__data__']")
        
        hkRootLevelContainer = self.dataroot.find("hkobject[@class='hkRootLevelContainer']") 
        
        self.readHKClass(hkRootLevelContainer)
        
        
        bpy.context.scene.collection.children.link(self.hkx_collection)
        
        
    


def ImportHKXFile(path):
    plugin_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    hkx_converter = os.path.join(plugin_dir, "bin", "HavokAssetCc.exe") # Gets the exe directory 
    print(hkx_converter)
    
    
    subprocess.run([hkx_converter, path, path + ".xml"])
    converted_hkx_file = path + ".xml"
    
    # Now we actually have some fun
    hkx = HKX()
    hkx.load(converted_hkx_file)
    
    