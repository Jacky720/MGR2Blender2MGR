# basically a wrapper for generate_data.py and write_wmb/__init__.py
from ...utils.ioUtils import create_wmb, close_wmb
from .generate_data import c_generate_data
from .write_wmb import *

import time

normals_flipped = False

def flip_all_normals():
    normals_flipped = True
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.data.flip_normals()
    print('Flipped normals of all meshes.')

def purge_unused_materials():
    for material in bpy.data.materials:
        if not material.users:
            print('Purging unused material:', material)
            bpy.data.materials.remove(material)

def prepare_blend():
    print('Preparing .blend File:')
    for obj in bpy.data.collections['WMB'].all_objects:
        if obj.type not in ['MESH', 'ARMATURE', 'EMPTY']:
            print(obj.type, obj.name)
            print('[-] Removed ', obj)
            bpy.data.objects.remove(obj)

def restore_blend():
    print('Restoring .blend File:')
    # Do shit here if needed
    print('EXPORT COMPLETE. :D')
    return {'FINISHED'}


def main(filepath, wmb4=True, collectionName="WMB", BALLIN=True):
    start_time = int(time.time())
    prepare_blend()

    wmb_file = create_wmb(filepath)

    if collectionName == "WMB": # Get sub-collection, one that isn't disabled.
        wmbLayerCollection = bpy.context.view_layer.layer_collection.children['WMB']
        subCollection = [x for x in wmbLayerCollection.children if x.is_visible][0]
        collectionName = subCollection.collection.name

    generated_data = c_generate_data(collectionName, BALLER=BALLIN)
    print('-=# All Data Generated. Writing WMB... #=-')
    create_wmb_header(wmb_file, generated_data, collectionName)

    print('Writing vertexGroups.')
    create_wmb_vertexGroups(wmb_file, generated_data)

    print('Writing batches.')
    create_wmb_batches(wmb_file, generated_data)
    
    print('Writing batch supplementary data.')
    create_wmb_batch_supplement(wmb_file, generated_data)
    
    if generated_data.bones is not None:
        print('Writing bones.')
        create_wmb_bones(wmb_file, generated_data)

    if hasattr(generated_data, 'boneIndexTranslateTable'):
        print('Writing boneIndexTranslateTable.')
        create_wmb_boneIndexTranslateTable(wmb_file, generated_data)

    if hasattr(generated_data, 'boneSet'):
        print('Writing boneSets.')
        create_wmb_boneSet(wmb_file, generated_data)

    print('Writing materials.')
    create_wmb_materials(wmb_file, generated_data)

    print('Writing textures.')
    #TODO
    create_wmb_textures(wmb_file, generated_data)

    print('Writing meshes.')
    create_wmb_meshes(wmb_file, generated_data)
    
    if generated_data.mystery is not None:
        print("God help us, writing that absurd mystery chunk.")
        create_wmb_mystery(wmb_file, generated_data)

    print('Finished writing. Closing file..')
    close_wmb(wmb_file, generated_data)

    end_time = int(time.time())
    export_duration = end_time - start_time
    export_min, export_sec = divmod(export_duration, 60)
    export_min = str(export_min).zfill(2)
    export_sec = str(export_sec).zfill(2)
    print(' - WMB generation took: %s:%s minutes.' % (export_min, export_sec))
    
    return {'FINISHED'}
