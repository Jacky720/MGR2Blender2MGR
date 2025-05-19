bl_info = {
    "name": "MGR2Blender2MGR (Metal Gear Rising Data Exporter)",
    "author": "Woeful_Wolf, RaiderB, Jacky720, Gaming with Portals, and Aura39",
    "version": (0, 2, 0),
    "blender": (3, 0, 0),
    "description": "Import/Export Various Metal Gear Rising Data files.",
    "category": "Import-Export"}


import bpy
from bpy.app.handlers import persistent
from . import preferences
from .dat_dtt.exporter import dat_dtt_ui_manager
from .utils.util import *
from .utils.utilOperators import RecalculateObjectIndices, RemoveUnusedVertexGroups, MergeVertexGroupCopies, \
    DeleteLooseGeometrySelected, DeleteLooseGeometryAll, RipMeshByUVIslands, ClearSelectedBoneIDs, RestoreImportPose
from .utils.visibilitySwitcher import enableVisibilitySelector, disableVisibilitySelector
from .utils import visibilitySwitcher
from .wta_wtp.exporter import wta_wtp_ui_manager
from .dat_dtt.importer.datImportOperator import ImportNierDtt, ImportNierDat
from .mot.exporter.motExportOperator import ExportNierMot
from .mot.importer.motImportOperator import ImportNierMot
from .mot.common.motUtils import getArmatureObject
from .mot.common.pl000fChecks import HidePl000fIrrelevantBones, RemovePl000fIrrelevantAnimations
from .wmb.exporter.wmbExportOperator import ExportMGRRWmb
from .wmb.exporter.wmbMaterialJSON import *
from .wmb.importer.wmbImportOperator import ImportNierWmb
from .scr.importer.scrImportOperator import ImportSCR
from .scr.exporter.scrExportOperator import ExportSCR
from .wta_wtp.importer.wtpImportOperator import ExtractNierWtaWtp
from .bxm.importer import physPanel
from .bxm.importer import gadImporter
from .wmb.materials import materialUI
from .hkx.importer import hkxImportOperator
from .path.importer import pathImportOperator
from .path.exporter import pathExportOperator
from .wmb import wmb_builder
from .wmb import lightmapPanel

class NierObjectMenu(bpy.types.Menu):
    bl_idname = 'OBJECT_MT_n2b2n'
    bl_label = 'MGR:R Tools'
    def draw(self, context):
        
        self.layout.operator(RecalculateObjectIndices.bl_idname, icon="LINENUMBERS_ON")
        self.layout.operator(RemoveUnusedVertexGroups.bl_idname, icon="GROUP_VERTEX")
        self.layout.operator(MergeVertexGroupCopies.bl_idname, icon="GROUP_VERTEX")
        self.layout.operator(DeleteLooseGeometrySelected.bl_idname, icon="EDITMODE_HLT")
        self.layout.operator(DeleteLooseGeometryAll.bl_idname, icon="EDITMODE_HLT")
        self.layout.operator(RipMeshByUVIslands.bl_idname, icon="UV_ISLANDSEL")
        self.layout.operator(RestoreImportPose.bl_idname, icon='OUTLINER_OB_ARMATURE')
        # self.layout.operator(wmb_builder.MakeNewWMB.bl_idname, icon='CUBE')
        self.layout.operator()
        
        armature = getArmatureObject()
        if armature is not None and armature.animation_data is not None and armature.animation_data.action is not None \
            and armature.name in { "pl0000", "pl000d", "pl0100", "pl010d" }:
            self.layout.operator(HidePl000fIrrelevantBones.bl_idname, icon="ARMATURE_DATA")
            self.layout.operator(RemovePl000fIrrelevantAnimations.bl_idname, icon="FCURVE")

class NierArmatureMenu(bpy.types.Menu):
    bl_idname = 'ARMATURE_MT_n2b2n'
    bl_label = 'MGR:R Tools'
    def draw(self, context):
        self.layout.operator(ClearSelectedBoneIDs.bl_idname, icon='BONE_DATA')

class IMPORT_MGR_HKXMenu(bpy.types.Menu):
    bl_label = "Physics"
    bl_idname = "IMPORT_MT_phys"

    def draw(self, context):
        pcoll = preview_collections["main"]
        self.layout.operator(hkxImportOperator.ImportMGRHavokPackfile.bl_idname, text="HAVOK Collision (.hkx)", icon_value=pcoll["havok"].icon_id)
        self.layout.operator(pathImportOperator.ImportMGRPath.bl_idname, text="Pathfinding Data (.bin)", icon_value=pcoll["raiden"].icon_id)

class IMPORT_MGR_MainMenu(bpy.types.Menu):
    bl_label = "MGR: Revengeance"
    bl_idname = "IMPORT_MT_main_menu"

    def draw(self, context):
        pcoll = preview_collections["main"]
        raiden_icon = pcoll["raiden"] 
        
        # self.layout.menu(IMPORT_MGR_HKXMenu.bl_idname, icon_value=pcoll["raiden"].icon_id)    
        self.layout.operator(ImportNierDat.bl_idname, text="Archive File (.dat, .dtt)", icon_value=raiden_icon.icon_id)
        self.layout.operator(ImportNierWmb.bl_idname, text="Model File (.wmb)", icon_value=raiden_icon.icon_id)
        self.layout.operator(ImportSCR.bl_idname, text="Stage/Level File (.scr)", icon_value=raiden_icon.icon_id)
        self.layout.operator(ImportNierMot.bl_idname, text="Animation (Motion) File (.mot)", icon_value=raiden_icon.icon_id)
        self.layout.operator(ExtractNierWtaWtp.bl_idname, text="Extract Textures (.wta, .wtp)", icon_value=raiden_icon.icon_id)
        self.layout.operator(gadImporter.ImportMGRGad.bl_idname, text="Lighting Information (.gad)", icon_value=raiden_icon.icon_id)

class EXPORT_MGR_MainMenu(bpy.types.Menu):
    bl_label = "MGR: Revengeance"
    bl_idname = "EXPORT_MT_main_menu"

    def draw(self, context):
        pcoll = preview_collections["main"]
        raiden_icon = pcoll["raiden"] 
        self.layout.operator(ExportMGRRWmb.bl_idname, text="Model File (.wmb)", icon_value=raiden_icon.icon_id)
        self.layout.operator(ExportSCR.bl_idname, text="Stage/Level File (.scr)", icon_value=raiden_icon.icon_id)
        self.layout.operator(ExportNierMot.bl_idname, text="Animation (Motion) File (.mot)", icon_value=raiden_icon.icon_id)
        # self.layout.operator(pathExportOperator.ExportMGRPath.bl_idname, text="Pathfinding Data (.bin)", icon_value=raiden_icon.icon_id)


def menu_func_import(self, context):
    pcoll = preview_collections["main"]
    raiden_icon = pcoll["raiden"] 
    
    self.layout.menu(IMPORT_MGR_MainMenu.bl_idname, icon_value=raiden_icon.icon_id)


def menu_func_export(self, context):
    pcoll = preview_collections["main"]
    raiden_icon = pcoll["raiden"] 
    
    self.layout.menu(EXPORT_MGR_MainMenu.bl_idname, icon_value=raiden_icon.icon_id)
    
    self.layout.operator_context = 'INVOKE_DEFAULT'
    
    
    

def menu_func_utils(self, context):
    pcoll = preview_collections["main"]
    raiden_icon = pcoll["raiden"]
    self.layout.menu(NierObjectMenu.bl_idname, icon_value=raiden_icon.icon_id)

def menu_func_editbone_utils(self, context):
    pcoll = preview_collections["main"]
    yorha_icon = pcoll["yorha"]
    self.layout.menu(NierArmatureMenu.bl_idname, icon_value=yorha_icon.icon_id)

classes = (
    ImportNierWmb,
    ImportSCR,
    ImportNierDtt,
    ImportNierDat,
    ImportNierMot,

    ExportMGRRWmb,
    ExportSCR,
    ExportNierMot,
    ExtractNierWtaWtp,
    
    NierObjectMenu,
    NierArmatureMenu,
    RecalculateObjectIndices,
    RemoveUnusedVertexGroups,
    MergeVertexGroupCopies,
    DeleteLooseGeometrySelected,
    DeleteLooseGeometryAll,
    RipMeshByUVIslands,
    ClearSelectedBoneIDs,
    RestoreImportPose,
    HidePl000fIrrelevantBones,
    RemovePl000fIrrelevantAnimations,
    
    WMBMaterialToJSON,
    WMBMaterialFromJSON,
    WMBCopyMaterialJSON,
    WMBPasteMaterialJSON,
    WMBMaterialJSONPanel,

    gadImporter.ImportMGRGad,
    
    hkxImportOperator.ImportMGRHavokPackfile,
    hkxImportOperator.ImportMGRHavokTagfile,
    
    pathImportOperator.ImportMGRPath,
    pathExportOperator.ExportMGRPath,

    wmb_builder.MakeNewWMB,
    #lightmapPanel.B2MLightmapEditor,
    lightmapPanel.B2MMakeLightmaps
    
    
)

preview_collections = {}

def register():
    # Custom icons
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    my_icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("raiden", os.path.join(my_icons_dir, "raiden.png"), 'IMAGE')
    pcoll.load("havok", os.path.join(my_icons_dir, "hvk.png"), 'IMAGE')
    preview_collections["main"] = pcoll

    from .utils.util import MGRVector4Property
    bpy.utils.register_class(MGRVector4Property)
    for cls in classes:
        bpy.utils.register_class(cls)
    materialUI.register()
    bpy.utils.register_class(IMPORT_MGR_MainMenu)
    bpy.utils.register_class(IMPORT_MGR_HKXMenu)
    bpy.utils.register_class(EXPORT_MGR_MainMenu)

    wta_wtp_ui_manager.register()
    dat_dtt_ui_manager.register()
    physPanel.register()
    preferences.register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_object.append(menu_func_utils)
    bpy.types.VIEW3D_MT_edit_armature.append(menu_func_editbone_utils)

    bpy.types.Object.collisionType = bpy.props.EnumProperty(name="Collision Type", items=collisionTypes, update=updateCollisionType)
    bpy.types.Object.UNKNOWN_collisionType = bpy.props.IntProperty(name="Unknown Collision Type", min=0, max=255, update=updateCollisionType)
    bpy.types.Object.slidable = bpy.props.BoolProperty(name="Slidable/Modifier")
    bpy.types.Object.surfaceType = bpy.props.EnumProperty(name="Surface Type", items=surfaceTypes)
    bpy.types.Material.wmb_mat_as_json = bpy.props.StringProperty(name="JSON")

    bpy.app.handlers.load_post.append(checkCustomPanelsEnableDisable)
    bpy.app.handlers.depsgraph_update_post.append(initialCheckCustomPanelsEnableDisable)

    bpy.types.Scene.selected_material = bpy.props.EnumProperty(
        name="Copy From Existing Material",
        description="Select a material",
        items=get_materials
    )

def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    materialUI.unregister()
    bpy.utils.unregister_class(IMPORT_MGR_MainMenu)
    bpy.utils.unregister_class(EXPORT_MGR_MainMenu)
    wta_wtp_ui_manager.unregister()
    dat_dtt_ui_manager.unregister()
    visibilitySwitcher.unregister()
    physPanel.unregister()
    preferences.unregister()
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_object.remove(menu_func_utils)
    bpy.types.VIEW3D_MT_edit_armature.remove(menu_func_editbone_utils)

    bpy.app.handlers.load_post.remove(checkCustomPanelsEnableDisable)
    if initialCheckCustomPanelsEnableDisable in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(initialCheckCustomPanelsEnableDisable)

@persistent
def checkCustomPanelsEnableDisable(_, __):
    if "WMB" in bpy.data.collections:
        enableVisibilitySelector()
    else:
        disableVisibilitySelector()

def initialCheckCustomPanelsEnableDisable(_, __):
    # during registration bpy.data is not yet available, so wait for first depsgraph update
    if hasattr(bpy.data, "collections"):
        checkCustomPanelsEnableDisable(_, __)
        bpy.app.handlers.depsgraph_update_post.remove(initialCheckCustomPanelsEnableDisable)

def migrateOldWmbCollection():
    # check if current file is an old wmb import
    if "hasMigratedToN2B2N" in bpy.context.scene:
        return
    if "WMB" in bpy.data.collections:
        return
    if "boundingBoxUVW" not in bpy.context.scene or "boundingBoxXYZ" not in bpy.context.scene:
        return
    if not any(["LOD_Level" not in obj for obj in bpy.data.objects]):
        return

    # migrate
    # find collection with WMB objects
    oldWmbColl: bpy.types.Collection = None
    for collection in bpy.context.scene.collection.children:
        if not any(["LOD_Level" in obj for obj in collection.all_objects]):
            continue
        oldWmbColl = collection
        break
    if oldWmbColl is None:
        return

    bpy.context.scene.collection.children.unlink(oldWmbColl)
    parentWmbColl = bpy.data.collections.new("WMB")
    bpy.context.scene.collection.children.link(parentWmbColl)
    parentWmbColl.children.link(oldWmbColl)
    
    bpy.context.scene["hasMigratedToN2B2N"] = True

    print("Migrated scene to new version")

def migrateDatDirs():
    dirTypes = [
        {
            "key": "DatDir",
            "newList": bpy.context.scene.DatContents
        },
        {
            "key": "DttDir",
            "newList": bpy.context.scene.DttContents
        }
    ]
    for dirType in dirTypes:
        if dirType["key"] not in bpy.context.scene or len(dirType["newList"]) > 0:
            continue
        datDir = bpy.context.scene[dirType["key"]]
        if os.path.isdir(datDir):
            if not importContentsFileFromFolder(datDir, dirType["newList"]):
                print("No dat_info.json or file_order.metadata found in " + datDir)

## Collision Extras
def setColourByCollisionType(obj):
    opacity = 1.0
    collisionType = int(obj.collisionType)
    if collisionType == 127:
        obj.color = [0.0, 1.0, 0.0, opacity]
    elif collisionType == 88:
        obj.color = [0.0, 0.5, 1.0, opacity]
    elif collisionType == 3:
        obj.color = [1.0, 0.5, 0.0, opacity]
    elif collisionType == 255:
        obj.color = [1.0, 0.0, 0.0, opacity]
    else:
        obj.color = [1.0, 0.45, 1.0, opacity]

def updateCollisionType(self, context):
    setColourByCollisionType(self)

collisionTypes = [
    ("-1", "UNKNOWN", ""),
    ("3", "Block Actors", "If modifier is enabled, this will not block players who are jumping (e.g. to prevent accidentally walking off ledges)."),
    ("88", "Water", ""),
    ("127", "Grabbable Block All", ""),
    ("255", "Block All", "")
]

# Identified by NSA Cloud
surfaceTypes = [
    ("-1", "UNKNOWN", ""),
    ("0", "Concrete1", ""),
    ("1", "Dirt", ""),
    ("2", "Concrete2", ""),
    ("3", "Metal Floor", ""),
    ("4", "Rubble", ""),
    ("5", "Metal Grate", ""),
    ("6", "Gravel", ""),
    ("7", "Rope Bridge", ""),
    ("8", "Grass", ""),
    ("9", "Wood Plank", ""),
    ("11", "Water", ""),
    ("12", "Sand", ""),
    ("13", "Rocky Gravel 1", ""),
    ("15", "Mud", ""),
    ("16", "Rocky Gravel 2", ""),
    ("17", "Concrete 3", ""),
    ("18", "Bunker Floor", ""),
    ("22", "Concrete 4", ""),
    ("23", "Car", ""),
    ("24", "Flowers", "")
]

if __name__ == '__main__':
    register()
