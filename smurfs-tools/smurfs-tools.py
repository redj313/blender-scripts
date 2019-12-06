# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Smurfs Tools",
    "description": "Basic Proxy tool for Compositor - Node Wrangler addon must be activated",
    "author": "redj",
    "version": (0, 0, 7),
    "blender": (2, 81, 0),
    "location": "Compositor > Properties Panel > Item",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Node",
}

import bpy

from bpy import data

import bpy.path as bpath

import os.path as opath

from bpy.props import (StringProperty,
                       PointerProperty,
                       )

from bpy.types import (Panel,
                       Operator,
                       PropertyGroup,
                       )

# ------------------------------------------------------------
# Properties
# ------------------------------------------------------------

class SmurfProps(PropertyGroup):
    suf1: StringProperty(
        name="A",
        description="Suffix used in the filenames of your currently loaded images (i.e. your low def proxy)",
        default="_lodef",
        maxlen=1024,
        )
    
    suf2: StringProperty(
        name="B",
        description="Suffix used in the filenames of your alternate images (i.e. your high def image)",
        default="_hidef",
        maxlen=1024,
        )

# -------------------------------------------------------------
# Fonctions
# -------------------------------------------------------------

def switch_suffix(a, b, scene, self):    
    tree = scene.node_tree
    num_switched = 0
    
    for nodes in tree.nodes:
        if nodes.type == 'IMAGE':
            if nodes.image:
                nodes.image.filepath = nodes.image.filepath.replace(a, b)
                nodes.image.name = nodes.image.name.replace(a, b)
                num_switched += 1
        
    self.report({'INFO'}, "Switched " + str(num_switched) + " images")
    print("Switched " + str(num_switched) + " images")

            
def transfer_img_res(image, scene, self):
    # Thanks to Vincent Gires for the following hack!
    if image.type == 'MULTILAYER':
        # HACK to get the resolution of a multilayer EXR through movieclip
        movieclip = data.movieclips.load(image.filepath)
        x, y = movieclip.size
        data.movieclips.remove(movieclip)
    else:
        x, y = image.size

    if scene.render.resolution_x == x and scene.render.resolution_y == y:
        self.report({'INFO'}, "Resolution already matching")
        print(f"Image and Render have same dimensions: {x} by {y}")

    else:
        # Passes the image's resolution to render resolution
        scene.render.resolution_x = x
        scene.render.resolution_y = y
        self.report({'INFO'}, "Render size changed")
        print(f"Render size set to {x} by {y}")


# -------------------------------------------------------------
# OPERATORS
# -------------------------------------------------------------

class SM_OT_SmurfSwitch1(Operator):
    bl_label = "Switch A --> B"
    bl_idname = "sm.smurfab"
    bl_description = "Replaces string A with string B in the image filename (to load an alternate version)"
        
    @classmethod
    def poll(cls, context):
        scene = context.scene
        smurf = scene.smurf
        tree = context.scene.node_tree
        tgt_nodes = []
        
        '''Checks if the string to be replaced (A) is contained in any of the images' filepath,
        and if the potential outcome of switching it to B would point to an existing file.
        '''
        for nodes in tree.nodes:
            if nodes.type == 'IMAGE':
                if nodes.image:
                    if smurf.suf1 in bpath.basename(nodes.image.filepath):
                        nodepath = bpath.abspath(nodes.image.filepath).replace(smurf.suf1, smurf.suf2)
                        if opath.isfile(nodepath):
                            tgt_nodes.append(nodes.name)        
        return tgt_nodes        
    
    def execute(self, context):
        scene = context.scene
        smurf = scene.smurf
        
        switch_suffix(smurf.suf1, smurf.suf2, scene, self)
        
        return {'FINISHED'}

class SM_OT_SmurfSwitch2(Operator):
    bl_label = "Switch B --> A"
    bl_idname = "sm.smurfba"
    bl_description = "Replaces string B with string A in the image filename"
    
    @classmethod
    def poll(cls, context):
        scene = context.scene
        smurf = scene.smurf
        tree = context.scene.node_tree
        tgt_nodes = []
        
        '''Checks if the string to be replaced (B) is contained in any of the images' filepath,
        and if the potential outcome of switching it to A would point to an existing file.
        '''
        for nodes in tree.nodes:
            if nodes.type == 'IMAGE':
                if nodes.image:
                    if smurf.suf2 in bpath.basename(nodes.image.filepath):
                        nodepath = bpath.abspath(nodes.image.filepath).replace(smurf.suf2, smurf.suf1)
                        if opath.isfile(nodepath):
                            tgt_nodes.append(nodes.name)        
        return tgt_nodes
    
    def execute(self, context):
        scene = context.scene
        smurf = scene.smurf
        
        switch_suffix(smurf.suf2, smurf.suf1, scene, self)
        
        return {'FINISHED'}
    
class SM_OT_TransferImageRes(Operator):
    bl_label = "Set Resolution From Active"
    bl_idname = "sm.smurfimgres"
    bl_description = "Automatically sets the render resolution from the active image node"
    
    @classmethod
    def poll(cls, context):
        tree = context.scene.node_tree
        
        # This operator will only be active if the active node is an image node with an image loaded.
        if tree.nodes.active.type == 'IMAGE':
            return tree.nodes.active.image
    
    def execute(self, context):
        scene = context.scene        
        tree = scene.node_tree
        
        transfer_img_res(tree.nodes.active.image, scene, self)
                
        return {'FINISHED'}
    
# --------------------------------------------------------------
# INTERFACE
# --------------------------------------------------------------

class SmurfPanel(bpy.types.Panel):
    bl_label = "Smurfs Tools"
    bl_idname = "NODE_PT_smurfs"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_category = "Item"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        smurf = scene.smurf
        rd = scene.render
        
        layout.label(text="Proxy Image Switch")
        
        layout.prop(smurf, "suf1")
        layout.prop(smurf, "suf2")
        
        row = layout.row(align=True)  

        row.operator(SM_OT_SmurfSwitch1.bl_idname, icon='LOOP_FORWARDS')
        row.operator(SM_OT_SmurfSwitch2.bl_idname, icon='LOOP_BACK')

        col = layout.column(align=True)

        col.separator()
        # The following operator is from the Node Wrangler addon - it has to be activated obviously.         
        col.operator(bpy.types.NODE_OT_nw_reload_images.bl_idname, icon='FILE_REFRESH')
        
        col.separator()
        col.separator()

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(rd, "resolution_x", text="Resolution X")
        col.prop(rd, "resolution_y", text="Resolution Y")
        col.prop(rd, "resolution_percentage", text="%")

        col.separator()

        col.operator(SM_OT_TransferImageRes.bl_idname, icon='NODE_SEL')

class ColorManagement(bpy.types.Panel):
    # Duplicate of the same panel from render properties - handy to access it from here
    bl_label = "Color Management"
    bl_idname = "NODE_PT_color_management"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_category = "Item"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        scene = context.scene
        view = scene.view_settings

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

        col = flow.column()
        col.prop(scene.display_settings, "display_device")

        col.separator()

        col.prop(view, "view_transform")
        col.prop(view, "look")

        col = flow.column()
        col.prop(view, "exposure")
        col.prop(view, "gamma")

        col.separator()
                
# --------------------------------------------------------------
# REGISTER
# --------------------------------------------------------------

classes = (
    SM_OT_SmurfSwitch1,
    SM_OT_SmurfSwitch2,
    SM_OT_TransferImageRes,
    SmurfProps,
    SmurfPanel,
    ColorManagement,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.smurf = PointerProperty(type=SmurfProps)
    
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.smurf

if __name__ == "__main__":
    register()