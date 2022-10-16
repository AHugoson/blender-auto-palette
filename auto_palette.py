bl_info = {
    "name": "Auto Palette",
    "author": "Aron Hugoson",
    "version": (1, 1, 2),
    "blender": (3, 3, 0),
    "location": "Material Properties",
    "description": "Combines materials into palette textures.",
    "warning": "Check documentation for compatibility info",
    "doc_url": "https://github.com/AHugoson/blender-auto-palette",
    "category": "Material",
}

import bpy
import math
import time
from bpy.types import Operator


def combine_bsdfs(obj, opt_metallic=True, opt_roughness=True, opt_emission=True):
    original_context = bpy.context.area.ui_type
    
    def lin2srgb(lin):
        if lin > 0.0031308:
            s = 1.055 * (pow(lin, (1.0 / 2.4))) - 0.055
        else:
            s = 12.92 * lin
        return s
    
    def paint_img_palette(img, colors, srgb=False):
        pixels = img.pixels

        for id, rgba in enumerate(colors):
            pixels[id*4] = lin2srgb(rgba[0]) if srgb else rgba[0]
            pixels[id*4+1] = lin2srgb(rgba[1]) if srgb else rgba[1]
            pixels[id*4+2] = lin2srgb(rgba[2]) if srgb else rgba[2]
        
        img.pixels = pixels
    
    def new_texImage(mat, img, pos):
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texImage.image = img
        texImage.interpolation = 'Closest'
        texImage.location = pos
        
        return texImage
    
    colors = []
    metal_rough = []
    emission = []
    
    for slot in obj.material_slots:
        bsdf = slot.material.node_tree.nodes['Principled BSDF']
        colors.append(bsdf.inputs['Base Color'].default_value)
        metallic_val = bsdf.inputs['Metallic'].default_value if opt_metallic else 0.0
        roughness_val = bsdf.inputs['Roughness'].default_value if opt_roughness else 0.0
        metal_rough.append([0.0, roughness_val, metallic_val])
        emission.append(bsdf.inputs['Emission'].default_value)

    # Smallest possible power of 2 image dimensions that fits all colors
    img_dim = 2**math.ceil(math.log(len(colors), 4))

    if f'{obj.name}_color_palette' in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[f'{obj.name}_color_palette'])
    if f'{obj.name}_rough_metal_palette' in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[f'{obj.name}_rough_metal_palette'])
    if f'{obj.name}_emission_palette' in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[f'{obj.name}_emission_palette'])

    bpy.ops.image.new(name=f'{obj.name}_color_palette', width=img_dim, height=img_dim)
    if opt_metallic or opt_roughness:
        bpy.ops.image.new(name=f'{obj.name}_rough_metal_palette', width=img_dim, height=img_dim)
    if opt_emission:
        bpy.ops.image.new(name=f'{obj.name}_emission_palette', width=img_dim, height=img_dim)
    
    color_img = bpy.data.images[f'{obj.name}_color_palette']
    if opt_metallic or opt_roughness:
        rough_metal_img = bpy.data.images[f'{obj.name}_rough_metal_palette']
    if opt_emission:
        emission_img = bpy.data.images[f'{obj.name}_emission_palette']
        
    paint_img_palette(color_img, colors, srgb=True)
    if opt_metallic or opt_roughness:
        paint_img_palette(rough_metal_img, metal_rough, srgb=False)
    if opt_emission:
        paint_img_palette(emission_img, emission, srgb=True)

    bpy.ops.object.mode_set(mode='EDIT')
    
    # Create UV map if none exists
    if not bpy.context.active_object.data.uv_layers.active:
        bpy.ops.mesh.uv_texture_add()
        
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    bpy.context.area.ui_type = 'UV'
    
    for i in range(len(bpy.context.object.material_slots)):
        bpy.context.object.active_material_index = i
        bpy.ops.object.material_slot_select()
        bpy.ops.uv.cursor_set(location=(0.5/img_dim + (1/img_dim)*(i%img_dim), 0.5/img_dim + (1/img_dim)*(i//img_dim)))
        bpy.ops.uv.snap_selected(target='CURSOR')
        bpy.ops.uv.snap_selected(target='PIXELS')
        bpy.ops.uv.select_all(action='DESELECT')
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    for i in range(len(bpy.context.object.material_slots)):
        bpy.ops.object.material_slot_remove()
    
    mat = bpy.data.materials.new(name="Palette")
    mat.use_nodes = True
    obj.data.materials.append(mat)
    bsdf_node = mat.node_tree.nodes["Principled BSDF"]
    output_node = mat.node_tree.nodes["Material Output"]
    
    color_tex_node = new_texImage(mat, color_img, (-600, 400))
    if opt_metallic or opt_roughness:
        rough_metal_tex_node = new_texImage(mat, rough_metal_img, (-600, 100))
        separate_color_node = mat.node_tree.nodes.new('ShaderNodeSeparateColor')
        separate_color_node.location = -300, 100
    if opt_emission:
        emission_tex_node = new_texImage(mat, emission_img, (-600, 700))
        add_shader_node = mat.node_tree.nodes.new('ShaderNodeAddShader')
        add_shader_node.location = 300, 400
        emission_node = mat.node_tree.nodes.new('ShaderNodeEmission')
        emission_node.location = 0, 500
        output_node.location = 500, 300
    
    mat.node_tree.links.new(bsdf_node.inputs['Base Color'], color_tex_node.outputs['Color'])
    if opt_metallic:
        mat.node_tree.links.new(bsdf_node.inputs['Metallic'], separate_color_node.outputs['Blue'])
    if opt_roughness:
        mat.node_tree.links.new(bsdf_node.inputs['Roughness'], separate_color_node.outputs['Green'])
    if opt_metallic or opt_roughness:
        mat.node_tree.links.new(separate_color_node.inputs['Color'], rough_metal_tex_node.outputs['Color'])
    if opt_emission:
        mat.node_tree.links.new(output_node.inputs['Surface'], add_shader_node.outputs[0])
        mat.node_tree.links.new(add_shader_node.inputs[1], bsdf_node.outputs['BSDF'])
        mat.node_tree.links.new(add_shader_node.inputs[0], emission_node.outputs['Emission'])
        mat.node_tree.links.new(emission_node.inputs['Color'], emission_tex_node.outputs['Color'])
    
    bpy.context.area.ui_type = original_context
    
    
class AUTO_PALETTE_Properties(bpy.types.PropertyGroup):
    include_metallic: bpy.props.BoolProperty(default=True, description="Include metallic values (creates a metallic roughness texture)")
    include_roughness: bpy.props.BoolProperty(default=True, description="Include roughness values (creates a metallic roughness texture)")
    include_emission: bpy.props.BoolProperty(default=True, description="Include emission values (creates an emission texture)")
    
    
class MATERIAL_OT_auto_palette(Operator):
    """Combines all materials into a single material using palette textures"""
    bl_idname = "material.auto_palette"
    bl_label = "Generate palette textures"
    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context):
        t0 = time.perf_counter()
        opt_metallic = bpy.context.scene.auto_palette.include_metallic
        opt_roughness = bpy.context.scene.auto_palette.include_roughness
        opt_emission = bpy.context.scene.auto_palette.include_emission
        
        active_obj = bpy.context.active_object
        combine_bsdfs(active_obj, opt_metallic, opt_roughness, opt_emission)
        
        print(f'Palette creation time: {time.perf_counter() - t0}')
        return {'FINISHED'}
    

class AUTO_PALETTE_PT_Panel(bpy.types.Panel):
    bl_label = "Auto Palette"
    bl_idname = "AUTO_PALETTE_PT_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        option_row = layout.row()
        action_button = layout.column()
        
        option_row.prop(context.scene.auto_palette, 'include_metallic', text="Metallic")
        option_row.prop(context.scene.auto_palette, 'include_roughness', text="Roughness")
        option_row.prop(context.scene.auto_palette, 'include_emission', text="Emission")

        obj = bpy.context.active_object
        if obj==None or obj.type != 'MESH':
            action_button.label(text="Can only operate on mesh objects.")
        elif len(obj.material_slots) == 0:
            action_button.label(text="No materials, nothing to bake.")
        else:
            action_button.operator('material.auto_palette', icon="TEXTURE")


def register():
    bpy.utils.register_class(MATERIAL_OT_auto_palette)
    bpy.utils.register_class(AUTO_PALETTE_PT_Panel)
    bpy.utils.register_class(AUTO_PALETTE_Properties)
    bpy.types.Scene.auto_palette = bpy.props.PointerProperty(type=AUTO_PALETTE_Properties)


def unregister():
    bpy.utils.unregister_class(MATERIAL_OT_auto_palette)
    bpy.utils.unregister_class(AUTO_PALETTE_PT_Panel)
    bpy.utils.unregister_class(AUTO_PALETTE_Properties)


if __name__ == "__main__":
    register()
