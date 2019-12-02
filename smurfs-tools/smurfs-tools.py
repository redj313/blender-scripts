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
    "version": (0, 0, 2),
    "blender": (2, 81, 0),
    "location": "Compositor > Properties Panel > Item",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Node",
}

import bpy

from bpy import data

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

class smurfProps(PropertyGroup):

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


def switch_suffix(a, b):
    
    tree = bpy.context.scene.node_tree
    
    for nodes in tree.nodes:
        if nodes.type == 'IMAGE':
            nodes.image.filepath = nodes.image.filepath.replace(a, b)
            nodes.image.name = nodes.image.name.replace(a, b)
            
def transferImageResolution(image):
    
    if image.type == 'MULTILAYER':
        # HACK to get the resolution of a multilayer EXR through movieclip
        movieclip = data.movieclips.load(image.filepath)
        x, y = movieclip.size
        data.movieclips.remove(movieclip)
    else:
        x, y = image.size
    #return x, y
    bpy.context.scene.render.resolution_x = x
    bpy.context.scene.render.resolution_y = y

# -------------------------------------------------------------
# OPERATORS
# -------------------------------------------------------------

class SM_OT_SmurfSwitch1(Operator):
    bl_label = "Switch A --> B"
    bl_idname = "sm.smurfab"
    bl_description = "Replaces string A with string B in the image filename (to load an alternate version)"
    
    def execute(self, context):
        scene = bpy.context.scene
        smurf = scene.smurf
        
        switch_suffix(smurf.suf1, smurf.suf2)
        
        return {'FINISHED'}

class SM_OT_SmurfSwitch2(Operator):
    bl_label = "Switch B --> A"
    bl_idname = "sm.smurfba"
    bl_description = "Replaces string B with string A in the image filename"
    
    def execute(self, context):
        scene = bpy.context.scene
        smurf = scene.smurf
        
        switch_suffix(smurf.suf2, smurf.suf1)
        
        return {'FINISHED'}
    
class SM_OT_transferImageResolution(Operator):
    bl_label = "Set Resolution From Active"
    bl_idname = "sm.smurfimgres"
    bl_description = "Automatically sets the render resolution from the active image node"
    
    @classmethod
    def poll(cls,context):
        
        tree = bpy.context.scene.node_tree
        
        return tree.nodes.active.type == 'IMAGE'
    
    def execute(self, context):
        
        tree = bpy.context.scene.node_tree
        
        transferImageResolution(tree.nodes.active.image)
                
        return {'FINISHED'}
    
# --------------------------------------------------------------
# INTERFACE
# --------------------------------------------------------------

class smurfPanel(bpy.types.Panel):
    # panel attributes
    bl_label = "Smurfs Tools"
    bl_idname = "NODE_PT_smurfs"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_category = "Item"
        
    # draw funtions
    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        smurf = scene.smurf
        rd = scene.render
        
        layout.label(text="Proxy Image Switch")
        
        #layout.use_property_split = True

        layout.prop(smurf, "suf1")
        layout.prop(smurf, "suf2")
        
        row = layout.row(align=True)  

        row.operator(SM_OT_SmurfSwitch1.bl_idname, icon='LOOP_FORWARDS')
        row.operator(SM_OT_SmurfSwitch2.bl_idname, icon='LOOP_BACK')

        col = layout.column(align=True)

        col.separator()        
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

        col.operator(SM_OT_transferImageResolution.bl_idname, icon='NODE_SEL')

class colorManagement(bpy.types.Panel):
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
    SM_OT_transferImageResolution,
    smurfProps,
    smurfPanel,
    colorManagement,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.smurf = PointerProperty(type=smurfProps)
    
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.smurf

if __name__ == "__main__":
    register()
