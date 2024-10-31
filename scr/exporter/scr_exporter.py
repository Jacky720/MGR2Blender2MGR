import bpy
import os, struct, shutil
from pathlib import Path
# Replace the export statement below with the correct path to your WMB exporter
from ...wmb.exporter import wmb_exporter  # Assuming wmb_exporter.py is in root/wmb/exporter
from ...dat_dtt.exporter import datExportOperator
from ...utils.ioUtils import *
import math

def main(file_path, do_ly2):
    head = os.path.split(file_path)[0]
    
    print('Beginning SCR generation')
    #print(file_path, context)
    
    # sort models
    sub_models = []
    prop_models = []
    hexdigits = "0123456789abcdef"
    for sub_model in bpy.data.collections['WMB'].children:
        name = sub_model.name
        if name[0:2] in {"ba", "bh", "bm"} and all(c in hexdigits for c in name[2:6]) and (len(name) == 6 or (len(name) == 10 and name[6] == "." and name[7:].isnumeric())):
            prop_models.append(sub_model)
        else:
            sub_models.append(sub_model)
    
    
    # generate scr data
    current_offset = 0x10 + 4 * len(sub_models)
    if (current_offset % 0x10 > 0):
        current_offset += 0x10 - (current_offset % 0x10)
    
    model_head_offsets = []
    model_offsets = []
    model_names = []
    model_translations = [] # 2d array
    
    # this should really not be needed
    if not os.path.exists(head + '/extracted_scr'):
        os.makedirs(head + '/extracted_scr')
    
    for sub_model in sub_models:
        model_head_offsets.append(current_offset)
        current_offset += 140 # header size
        if (current_offset % 0x80 > 0):
            current_offset += 0x80 - (current_offset % 0x80)
        model_offsets.append(current_offset)
        name = sub_model.name
        model_names.append(name)
        
        translation = [0] * 27
        sample_mesh = sub_model.all_objects[0]
        translation[0] = sample_mesh.location.x
        translation[1] = sample_mesh.location.z
        translation[2] = -sample_mesh.location.y
        
        translation[3] = sample_mesh.rotation_euler.x - math.radians(90)
        translation[4] = sample_mesh.rotation_euler.z
        translation[5] = sample_mesh.rotation_euler.y
        
        translation[6] = sample_mesh.scale.x
        translation[7] = sample_mesh.scale.z
        translation[8] = sample_mesh.scale.y
        
        if "mystery_int16s" in sub_model:
            translation[9:] = list(sub_model["mystery_int16s"])
        else:
            print("WARN: WMB model lacks some mystery data in collection")
        
        model_translations.append(translation)
        
        wmb_path = head + "/extracted_scr/" + name + ".wmb"
        export_models(wmb_path, name)
        current_offset += os.path.getsize(wmb_path) # file size
        if (current_offset % 0x20 > 0):
            current_offset += 0x20 - (current_offset % 0x20)
        
        
        
    
    print('Beginning SCR write')
    with open(file_path, 'wb') as f:
        # header
        write_string(f, 'SCR')
        write_uInt16(f, 6) # TODO handle
        write_uInt16(f, len(sub_models))
        write_uInt32(f, 0x10) # offsets offset
        f.seek(0x10)
    
        for offset in model_head_offsets:
            write_uInt32(f, offset)
        print('Offsets written')
    
        for i, offset in enumerate(model_head_offsets):
            f.seek(offset)
            write_uInt32(f, model_offsets[i])
            write_string(f, model_names[i])
            f.seek(offset + 4 + 64) # string is padded to 64 bytes
            for val in model_translations[i][:9]:
                print(val)
                write_float(f, val)
            for val in model_translations[i][9:]:
                write_uInt16(f, val)
            print('Model header written for', model_names[i])
            
            # write model
            f.seek(model_offsets[i])
            wmb_file_path = f"{head}/extracted_scr/{model_names[i]}.wmb"
            with open(wmb_file_path, 'rb') as f2:
                f.write(f2.read())
            print('Model written')
    
    if do_ly2:
        # prop export
        # bad practice but I'll be, uh, not making an LY2 format
        ly2 = open(file_path[:-3] + "ly2", "wb")
        ly2.write(b"LY2\x00")
        
        print("Saving props")
        
        prop_types = sorted(list(set([x.name[0:6] for x in prop_models])))
        WMBCol = bpy.data.collections["WMB"]
        instancesPointer = 0x14 + 20 * len(prop_types)
        ly2MysteryPointer = instancesPointer + 40 * len(prop_models)
        #ly2MysteryPointer += 16 - (ly2MysteryPointer % 16)
        
        ly2.write(struct.pack("<IIII", WMBCol["ly2Flags"], len(prop_types), ly2MysteryPointer, len(WMBCol["ly2OtherFlags"])))
        ly2.seek(0x14) # start of main data
        for propType in prop_types:
            if "flags" not in bpy.data.collections[propType]:
                bpy.data.collections[propType]["flags"] = [0, 0]
            ly2.write(struct.pack("<I", bpy.data.collections[propType]["flags"][0])) # flags 1
            ly2.write(struct.pack("<I", bpy.data.collections[propType]["flags"][1])) # flags 2
            ly2.write(bytes(propType[0:2], "ascii"))
            ly2.write(struct.pack("<H", int(propType[2:6], 16)))
            # We don't write edited props; only their positions
            
            ly2.write(struct.pack("<I", instancesPointer))
            models_of_type = sorted([x for x in prop_models if x.name[0:6] == propType], key=lambda x: x.name)
            ly2.write(struct.pack("<I", len(models_of_type)))
            resumePos = ly2.tell()
            
            ly2.seek(instancesPointer)
            for modelCol in models_of_type:
                model = [x for x in modelCol.all_objects if x.type == "MESH"][0]
                ly2.write(struct.pack("<fff", model.location[0], model.location[2], -model.location[1]))
                ly2.write(struct.pack("<fff", model.scale[0], model.scale[1], model.scale[2]))
                rotY = model.rotation_euler[2] * 0x80 / 3.1415926535 # I do not claim to understand.
                ly2.write(struct.pack("<fBBBBfi", 0, int(rotY % 256), 0, 0, 0, 0, -1))
                instancesPointer += 40
                
            
            ly2.seek(resumePos)
        
        ly2.seek(ly2MysteryPointer)
        for i in range(len(WMBCol["ly2OtherFlags"])):
            ly2.write(struct.pack("<I", WMBCol["ly2OtherFlags"][i]))
            ly2.write(struct.pack("<I", WMBCol["ly2MysteryB"][i]))
            ly2.write(struct.pack("<I", WMBCol["ly2MysteryC"][i]))
        
        ly2.close()
        
    
    return {'FINISHED'}

def export_models(file_path, name):
    wmb_exporter.main(file_path, True, name)

def reset_blend():
    #bpy.ops.object.mode_set(mode='OBJECT')
    for collection in bpy.data.collections:
        for obj in collection.objects:
            collection.objects.unlink(obj)
        bpy.data.collections.remove(collection)
    for bpy_data_iter in (bpy.data.objects, bpy.data.meshes, bpy.data.lights, bpy.data.cameras, bpy.data.libraries):
        for id_data in bpy_data_iter:
            bpy_data_iter.remove(id_data)
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    for amt in bpy.data.armatures:
        bpy.data.armatures.remove(amt)
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)
        obj.user_clear()