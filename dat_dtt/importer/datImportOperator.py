import os

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

# Add this import statement at the top of the file
from ...scr.importer import scr_importer

from ...consts import DAT_EXTENSIONS
from ...col.exporter.col_ui_manager import enableCollisionTools
from ...utils.visibilitySwitcher import enableVisibilitySelector
from ...utils.util import setExportFieldsFromImportFile, ShowMessageBox

def ImportData(only_extract, filepath, transform=None):
    print("Importing data...")
    extension = os.path.splitext(filepath)[1]
    
    # This is a much better naming scheme
    head = os.path.split(filepath)[0]
    filename_with_extension = os.path.split(filepath)[1]
    filename_without_extension = filename_with_extension[:-4]
    extract_dir = os.path.join(head, 'nier2blender_extracted')
    
    dat_filepath = os.path.join(head, filename_without_extension + '.dat')
    dtt_filepath = os.path.join(head, filename_without_extension + '.dtt') 
    
    dtt_filename = "" # Initalization
    dat_filename = ""
    
    from . import dat_unpacker
    print("DAT Path: " + dat_filepath)
    if os.path.isfile(dat_filepath):
        dat_filename = dat_unpacker.main(dat_filepath, os.path.join(extract_dir, filename_without_extension + '.dat'), dat_filepath)
    print("DTT Path: " + dtt_filepath)
    if os.path.isfile(dtt_filepath):
        dtt_filename = dat_unpacker.main(dtt_filepath, os.path.join(extract_dir, filename_without_extension + '.dtt'), dtt_filepath)
    
    if (dat_filename == "" and dtt_filename == ""):
        print("I have no idea how you managed to select a DAT or DTT if you had neither")
    if (not os.path.isfile(dat_filepath) and os.path.isfile(dtt_filepath)):
        print("Did you just type random nonsense into the file select?")
    if (dat_filename == False and dtt_filename == False):
        print("Apparently, both the DAT and DTT associated with your selection are empty.")
        
    
    scr_mode = False
    wmb_mode = False
    wmb_ext = ".dat"
    scr_ext = ".dat"
    
    if (dtt_filename == False):
        # I dunno what this does but in the forefathers I trust
        dtt_filename = dat_filename[:10]
        
    wmb_files = [x for x in os.listdir(os.path.join(extract_dir, filename_without_extension + '.dat')) if os.path.splitext(x)[1] == ".wmb"]
    if (len(wmb_files) == 0):
        # Last chance to show yourself
        print("Attempting to find WMB in DTT (fruitless)")
        if (os.path.exists(os.path.join(extract_dir, filename_without_extension + '.dtt'))):
            wmb_files = [x for x in os.listdir(os.path.join(extract_dir, filename_without_extension + '.dtt')) if os.path.splitext(x)[1] == ".wmb"]
            wmb_ext = ".dtt"

    scr_files = [x for x in os.listdir(os.path.join(extract_dir, filename_without_extension + '.dat')) if os.path.splitext(x)[1] == ".scr"]

    if (len(wmb_files) > 0):
        wmb_mode = True
    elif (len(scr_files) == 0):
        # Last chance to show yourself
        print("Attempting to find SCR in DTT (fruitless)")
        if os.path.exists(os.path.join(extract_dir, filename_without_extension + '.dtt')):
            scr_files = [x for x in os.listdir(os.path.join(extract_dir, filename_without_extension + '.dtt')) if os.path.splitext(x)[1] == ".scr"]
            scr_ext = ".dtt"

    if (len(scr_files) > 0):
        scr_mode = True

    print("SCR Files: " + str(scr_files))
    print("WMB Files: " + str(wmb_files))

    # Phase Loader
    if (os.path.exists(os.path.join(extract_dir, filename_without_extension + '.dat', filename_without_extension + "_sub.bxm"))):
        print("Loading " + os.path.join(extract_dir, filename_without_extension + '.dat', filename_without_extension + "_sub.bxm"))
        from ...bxm.common.bxm import bxmToXml
        import xml.etree.ElementTree as ET
        
        bxmroot = bxmToXml(os.path.join(extract_dir, filename_without_extension + '.dat', filename_without_extension + "_sub.bxm"))
        bxtext = bxmroot.find(".//RoomNo").text
        base_data_001 = os.path.dirname(os.path.dirname(extract_dir))
        print(base_data_001)
        
        for rooms in bxtext.split(" "):
            stage_folder = "st" + rooms[1]
            print("Loading room: " + stage_folder + "\\" + rooms + ".dat")
            ImportData(False, os.path.join(base_data_001, stage_folder, rooms + ".dat"))
            
    
    # WTA/WTP
    wtaPath = os.path.join(extract_dir, filename_without_extension + '.dat', filename_without_extension + '.wta')
    wtpPath = os.path.join(extract_dir, filename_without_extension + '.dtt', filename_without_extension + '.wtp')
    if os.path.isfile(wtaPath) and os.path.isfile(wtpPath):
        texturesExtractDir = os.path.join(extract_dir, filename_without_extension + '.dtt', "textures")
        from ...wta_wtp.importer import wtpImportOperator
        wtpImportOperator.extractFromWta(wtaPath, wtpPath, texturesExtractDir)

    if only_extract:
        return {'FINISHED'}

    setExportFieldsFromImportFile(filepath, True)
    enableVisibilitySelector()
    
    

    if scr_mode:
        # SCR but new and improved
        if filename_without_extension + ".scr" in scr_files:
            scr_files = [filename_without_extension + ".scr"]
        scr_filepath = os.path.join(extract_dir, filename_without_extension + scr_ext, scr_files[0])
        print("WMB Path: " + scr_filepath)
        from ...scr.importer import scr_importer
        scr_importer.ImportSCR.main(scr_filepath, False)
    if wmb_mode:
        # WMB
        if filename_without_extension + ".wmb" in wmb_files:
            wmb_files = [filename_without_extension + ".wmb"]
        wmb_filepath = os.path.join(extract_dir, filename_without_extension + wmb_ext, wmb_files[0])
        print("WMB Path: " + wmb_filepath)
        from ...wmb.importer import wmb_importer
        wmb_importer.main(only_extract, wmb_filepath, transform)
    
    
    
    return {'FINISHED'}
    

# Legacy Function
def importDtt(only_extract, filepath, transform=None):
    head = os.path.split(filepath)[0]
    tail = os.path.split(filepath)[1]
    tailless_tail = tail[:-4]
    dat_filepath = os.path.join(head, tailless_tail + '.dat')
    extract_dir = os.path.join(head, 'nier2blender_extracted')
    from . import dat_unpacker
    if os.path.isfile(dat_filepath):
        alt_filename = dat_unpacker.main(dat_filepath, os.path.join(extract_dir, tailless_tail + '.dat'), dat_filepath)   # dat
    else:
        print('DAT not found. Only extracting DTT. (No materials, collisions or layouts will automatically be imported)')
    
    last_filename = dat_unpacker.main(filepath, os.path.join(extract_dir, tailless_tail + '.dtt'), filepath)       # dtt
    if last_filename == False: # empty dtt
        last_filename = alt_filename[:10]
        # cheating but this is already an error case
        # (two chars prefix, four chars ID, four chars filetype/discard)
    
    # try a bunch of methods of finding the filepath
    wmb_filepath = os.path.join(extract_dir, tailless_tail + '.dtt', last_filename[:-4] + '.wmb')
    if not os.path.exists(wmb_filepath): # if not in dtt, then must be in dat
        wmb_filepath = os.path.join(extract_dir, tailless_tail + '.dat', last_filename[:-4] + '.wmb')
    if not os.path.exists(wmb_filepath): # try looking based on the dat name
        wmb_filepath = os.path.join(extract_dir, tailless_tail + '.dat', tailless_tail + '.wmb')
    # if not in dat, must be an scr
    scr_mode = False
    if not os.path.exists(wmb_filepath):
        scr_mode = True
        print("Could not find WMB at %s, switching to SCR" % wmb_filepath)
        scr_filepath = os.path.join(extract_dir, tailless_tail + '.dat', last_filename[:-4].split("scr")[0] + '.scr')
        if not os.path.exists(scr_filepath): # try based on the dat name
            scr_filepath = os.path.join(extract_dir, tailless_tail + '.dat', tailless_tail + '.scr')
        if not os.path.exists(scr_filepath):
            ly2_filepath = scr_filepath[:-4] + ".ly2"
            if os.path.exists(ly2_filepath): # props only
                print("Found prop list, loading that")
            else:
                sub_bxm_filepath = scr_filepath[:-7] + "sub.bxm"
                if (os.path.exists(sub_bxm_filepath)):
                    print("Found a phase file, loading that")
                else:
                    
                    print("Could not find model file in DAT! Please import WMB manually.")
                    ShowMessageBox("Could not find model file in DAT! Please import WMB manually.", "No Model Found", "ERROR")
                    only_extract = True

    # WTA/WTP
    wtaPath = os.path.join(extract_dir, tailless_tail + '.dat', tailless_tail + '.wta')
    wtpPath = os.path.join(extract_dir, tailless_tail + '.dtt', tailless_tail + '.wtp')
    if os.path.isfile(wtaPath) and os.path.isfile(wtpPath):
        texturesExtractDir = os.path.join(extract_dir, tailless_tail + '.dtt', "textures")
        from ...wta_wtp.importer import wtpImportOperator
        wtpImportOperator.extractFromWta(wtaPath, wtpPath, texturesExtractDir)

    if only_extract:
        return {'FINISHED'}

    setExportFieldsFromImportFile(filepath, True)
    enableVisibilitySelector()

    # SCR
    #def execute(self, context):
    #    if self.filepath.lower().endswith('.scr'):
    #        return scr_importer.main(self.filepath)
    #    else:
    #        return importDtt(self.only_extract, self.filepath)
    
    # SCR but new and improved
    if scr_mode:
        from ...scr.importer import scr_importer
        scr_importer.ImportSCR.main(scr_filepath, False)
    else:
        # WMB
        from ...wmb.importer import wmb_importer
        wmb_importer.main(only_extract, wmb_filepath, transform)

    # COL
    col_filepath = os.path.join(extract_dir, tailless_tail + '.dat', tailless_tail + '.col')
    if os.path.isfile(col_filepath):
        from ...col.importer import col_importer
        col_importer.main(col_filepath)
        enableCollisionTools()

    # LAY
    lay_filepath = os.path.join(extract_dir, tailless_tail + '.dat', 'Layout.lay')
    if os.path.isfile(lay_filepath):
        from ...lay.importer import lay_importer
        lay_importer.main(lay_filepath)

    return {'FINISHED'}

class ImportNierDtt(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata DTT (and DAT) File.'''
    bl_idname = "import_scene.dtt_data"
    bl_label = "Import DTT (and DAT) Data"
    bl_options = {'PRESET'}
    filename_ext = ".dtt"
    filter_glob: StringProperty(default="*.dtt", options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)
    bulk_import: bpy.props.BoolProperty(name="Bulk Import All DTT/DATs In Folder (Experimental)", default=False)
    only_extract: bpy.props.BoolProperty(name="Only Extract DTT/DAT Contents. (Experimental)", default=False)

    def execute(self, context):
        print("Unpacking", self.filepath)
        from ...wmb.importer import wmb_importer
        if self.reset_blend and not self.only_extract:
            wmb_importer.reset_blend()
        if self.bulk_import:
            folder = os.path.split(self.filepath)[0]
            for filename in os.listdir(folder):
                if filename[-4:] == '.dtt':
                    try:
                        filepath = os.path.join(folder, filename)
                        print("\nImporting", filepath)
                        ImportData(self.only_extract, filepath)
                    except:
                        print('ERROR: FAILED TO IMPORT', filename)
            return {'FINISHED'}

        else:
            return ImportData(self.only_extract, self.filepath)
        


class ImportNierDat(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata DAT File.'''
    bl_idname = "import_scene.dat_data"
    bl_label = "Import DAT/DTT Data"
    bl_options = {'PRESET'}
    filename_ext = ".dat;.dtt"
    filter_glob: StringProperty(default=";".join([f"*{ext}" for ext in DAT_EXTENSIONS]), options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)
    bulk_import: bpy.props.BoolProperty(name="Bulk Import All DTT/DATs In Folder", default=False)
    only_extract: bpy.props.BoolProperty(name="Only Extract DTT/DAT Contents", default=False)

    def doImport(self, onlyExtract, filepath):
        head = os.path.split(filepath)[0]
        tail = os.path.split(filepath)[1]
        ext = tail[-4:]
        tailless_tail = tail[:-4]
        dat_filepath = os.path.join(head, tailless_tail + ext)
        extract_dir = os.path.join(head, 'nier2blender_extracted')
        from . import dat_unpacker
        if os.path.isfile(dat_filepath):
            dat_unpacker.main(dat_filepath, os.path.join(extract_dir, tailless_tail + ext), dat_filepath)   # dat

        if onlyExtract:
            return {'FINISHED'}

        setExportFieldsFromImportFile(filepath, True)

        # COL
        col_filepath = os.path.join(extract_dir, tailless_tail + '.dat', tailless_tail + '.col')
        if os.path.isfile(col_filepath):
            from ...col.importer import col_importer
            col_importer.main(col_filepath)
            enableCollisionTools()

        # LAY
        lay_filepath = os.path.join(extract_dir, tailless_tail + '.dat', 'Layout.lay')
        if os.path.isfile(lay_filepath):
            from ...lay.importer import lay_importer
            lay_importer.main(lay_filepath)

        return {'FINISHED'}

    def execute(self, context):
        print("Unpacking", self.filepath)
        from ...wmb.importer import wmb_importer
        if self.reset_blend and not self.only_extract:
            wmb_importer.reset_blend()
        firstModel = ImportData(self.only_extract, self.filepath)
        if self.bulk_import:
            folder = os.path.split(self.filepath)[0]
            for filename in os.listdir(folder):
                if filename[-4:] == '.dat':
                    try:
                        filepath = os.path.join(folder, filename)
                        if filepath != self.filepath: # Already got that one
                            ImportData(self.only_extract, filepath)
                    except:
                        print('ERROR: FAILED TO IMPORT', filename)
            return {'FINISHED'}
        return firstModel

