# Auto Palette

A Blender addon that combines separate materials into a single material with palette textures. The output follows the metal/rough PBR workflow [compatible with glTF 2.0](https://docs.blender.org/manual/en/2.80/addons/io_scene_gltf2.html#materials).

## Limitations

Currently limited to use with Principled BSDF materials with unconnected input sockets.

## Installation

Go to Edit -> Preferences, select Add-ons and press the 'Install...' button, then browse to the auto_palette.py file.

## How to use it

Make sure that the object you want to use is active, and go to the material properties window. The object in this example has several materials (all principled BSDF) with varying color, metallic, roughness, and emission values.

![image](https://user-images.githubusercontent.com/7094426/154842724-51a0d372-314a-4b57-b120-e7ea7c1de1e5.png)

Scroll down in the material properties window and you will see the Auto Palette panel, press the button to start generating the textures.

![image](https://user-images.githubusercontent.com/7094426/154842859-622b06ca-c2ff-4584-9b69-0e4b0a29dc72.png)

When the textures have been generated, the materials will be replaced by a new 'Palette' material.

![image](https://user-images.githubusercontent.com/7094426/154843301-b4cb6fe4-428a-4cbc-bcd6-350c3ed92f9e.png)

This material will be set up to use the generated palette textures.

![image](https://user-images.githubusercontent.com/7094426/154843432-92af4f13-5c46-491c-952c-5d465ff0c48b.png)

The UV mapped palette textures will look like the images below. The image dimensions will be the smallest possible power of two that fits all material values, in this case 4x4 px.

| Color | Roughness + Metallic | Emission |
| ----  | -------------------- | -------- |
| ![image](https://user-images.githubusercontent.com/7094426/154844014-c22f21f1-5129-4a3e-9207-708777da1960.png) | ![image](https://user-images.githubusercontent.com/7094426/154844025-d464b256-397a-44e0-a4d8-7066e4b9d411.png) | ![image](https://user-images.githubusercontent.com/7094426/154844042-5bf4ba4b-0a55-422d-8b66-f160597585d5.png) |
