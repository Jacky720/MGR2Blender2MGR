import bpy, bmesh, math, mathutils

import xml.etree.ElementTree as ET
from ..common.bxm import bxmToXml, xmlToBxm

def exportCLH(filepath):
    xml = ET.Element("CLOTH_AT")
    bpy.context.scene.clh_clothatnum = len(bpy.context.scene.clh_clothatwk)
    ET.SubElement(xml, "CLOTH_AT_NUM").text = str(bpy.context.scene.clh_clothatnum)

    xml_clothatwk_list = ET.SubElement(xml, "CLOTH_AT_WK_LIST")
    for cloth_at_wk_item in bpy.context.scene.clh_clothatwk:
        xml_clothatwk = ET.SubElement(xml_clothatwk_list, "CLOTH_AT_WK")
        ET.SubElement(xml_clothatwk, "p1").text = cloth_at_wk_item.p1
        ET.SubElement(xml_clothatwk, "p2").text = cloth_at_wk_item.p2
        ET.SubElement(xml_clothatwk, "weight").text = str(cloth_at_wk_item.weight)
        ET.SubElement(xml_clothatwk, "radius").text = str(cloth_at_wk_item.radius)
        ET.SubElement(xml_clothatwk, "offset1").text = " ".join([str(x) for x in cloth_at_wk_item.offset1])
        ET.SubElement(xml_clothatwk, "offset2").text = " ".join([str(x) for x in cloth_at_wk_item.offset2])
        ET.SubElement(xml_clothatwk, "capsule").text = str(int(cloth_at_wk_item.capsule))

    xmlToBxm(xml, filepath)