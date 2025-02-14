
import bpy, bmesh, math, mathutils

import xml.etree.ElementTree as ET
from ..common.bxm import bxmToXml, xmlToBxm

def exportCLP(filepath):
    # Create XML from blender data
    xml = ET.Element("CLOTH")
    xml_clothheader = ET.SubElement(xml, "CLOTH_HEADER")
    xml_clothwk_list = ET.SubElement(xml, "CLOTH_WK_LIST")
    
    # Header
    clothheader = bpy.context.scene.clp_clothheader
    # Update header m_Num
    clothheader.m_num = len(bpy.context.scene.clp_clothwk)
    ET.SubElement(xml_clothheader, "m_Num").text = str(clothheader.m_num)
    ET.SubElement(xml_clothheader, "m_LimitSpringRate").text = str(clothheader.m_limit_spring_rate)
    ET.SubElement(xml_clothheader, "m_SpdRate").text = str(clothheader.m_spd_rate)
    ET.SubElement(xml_clothheader, "m_Stretchy").text = str(clothheader.m_stretchy)
    ET.SubElement(xml_clothheader, "m_BundleNum").text = str(clothheader.m_bundle_num)
    ET.SubElement(xml_clothheader, "m_BundleNum2").text = str(clothheader.m_bundle_num2)
    ET.SubElement(xml_clothheader, "m_Thick").text = str(clothheader.m_thick)
    ET.SubElement(xml_clothheader, "m_GravityVec").text = " ".join([str(x) for x in clothheader.m_gravity_vec])
    ET.SubElement(xml_clothheader, "m_GravityPartsNo").text = str(clothheader.m_gravity_parts_no)
    ET.SubElement(xml_clothheader, "m_FirstBundleRate").text = str(clothheader.m_first_bundle_rate)
    ET.SubElement(xml_clothheader, "m_WindVec").text = " ".join([str(x) for x in clothheader.m_wind_vec])
    ET.SubElement(xml_clothheader, "m_WindPartsNo").text = str(clothheader.m_wind_parts_no)
    ET.SubElement(xml_clothheader, "m_WindOffset").text = " ".join([str(x) for x in clothheader.m_wind_offset])
    ET.SubElement(xml_clothheader, "m_WindSin").text = str(clothheader.m_wind_sin)
    ET.SubElement(xml_clothheader, "m_HitAdjustRate").text = str(clothheader.m_hit_adjust_rate)
    ET.SubElement(xml_clothheader, "m_OriginalRate").text = str(clothheader.m_original_rate)
    ET.SubElement(xml_clothheader, "m_ParentGravity").text = str(clothheader.m_parent_gravity)
    ET.SubElement(xml_clothheader, "m_FixAxis").text = str(clothheader.m_fix_axis)
    ET.SubElement(xml_clothheader, "m_bNoStretchy").text = str(int(clothheader.m_b_no_stretchy))
    ET.SubElement(xml_clothheader, "m_bWorldWindEnable").text = str(int(clothheader.m_b_world_wind_enable))
    ET.SubElement(xml_clothheader, "m_bAtCenter").text = str(int(clothheader.m_b_at_center))
    ET.SubElement(xml_clothheader, "m_bLateAddMode").text = str(int(clothheader.m_b_late_add_mode))
    ET.SubElement(xml_clothheader, "m_ExpandMax").text = str(clothheader.m_expand_max)

    # Cloth List
    cloth_wk = bpy.context.scene.clp_clothwk
    for cloth_wk_item in cloth_wk:
        xml_clothwk = ET.SubElement(xml_clothwk_list, "CLOTH_WK")
        ET.SubElement(xml_clothwk, "no").text = cloth_wk_item.no
        ET.SubElement(xml_clothwk, "noUp").text = cloth_wk_item.no_up
        ET.SubElement(xml_clothwk, "noDown").text = cloth_wk_item.no_down
        ET.SubElement(xml_clothwk, "noSide").text = cloth_wk_item.no_side
        ET.SubElement(xml_clothwk, "noPoly").text = cloth_wk_item.no_poly
        ET.SubElement(xml_clothwk, "noFix").text = cloth_wk_item.no_fix
        ET.SubElement(xml_clothwk, "rotLimit").text = str(cloth_wk_item.rot_limit)
        ET.SubElement(xml_clothwk, "offset").text = " ".join([str(x) for x in cloth_wk_item.offset])
        ET.SubElement(xml_clothwk, "m_OriginalRate").text = str(cloth_wk_item.m_original_rate)

    # Write BXM to file
    xmlToBxm(xml, filepath)