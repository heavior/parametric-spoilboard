# Parametric model for generating CNC spoilboards and Sainsmart Genmitsu 3030-Pro cnc bed grid pattern

It has openSCAD model (outdated) and Autodesk Fusion 360 model (supported)

This repository is for generating spoilboards for CNC machines that have flat beds with grids of holes instead of slots

DIY spoilboard is cheaper and can be tuned to your needs. You can:
* use thinner spoilboard to save some vertical height
* choose alternatives to MDF such as plywood or plastic
* customise board size for a specific job
* position on the CNC bed as you want

This design relies on original threaded holes on the CNC bed for mounting, it does not use threaded incerts in the  sheet. If you prefer threaded incerts, modify the code as you need.

This model supports two manufactaruing options:
* Make CNC do all the work
* Use CNC to mark the grid, and then complete the job with a drill
Either option works well, because through holes do not require absolute precision.

# How to use:
Open Spoilboard.scad if you are using OpenSCAD, or Spoliboard.py if you are using Autodesk Fusion 360
Then read the comments in the file, you'll need to tune parameters to generate model, and then setup operations in your CAM software 

# Available renders:
If you want quick access to the STL files, and don't want to play with scripts, check out these renders.
Please note that your might have an MDF board with different dimensions, different screws and otherwise different preferences, and you might have to tune the models in your favoride CAD software. I'd recommend tuning everything in OpenSCAD

renders/3030-cncbed.stl - 3D model of Sainsmart Genmitsu 3030-pro cnc mill
renders/3030-spoilboard-through.stl - 3D model of a spoilboard with through holes and countersink
renders/3030-spoilboard-drill.stl - 3D model with only drill marks for all the holes

# Supproted models
This paramteric model will work to generate any pattern of holes (not continous slots).

Included configuration:
* Sainsmart Genmitsu 3030-Pro

If you find this model useful, and you have traced a hole pattern from a different cnc model, please consider sharing the new configuration back to the community.

# Links
Also available in Grabcad community: https://grabcad.com/library/parametric-spoilboard-and-pattern-for-genmitsu-sainsmart-3030-pro-cnc-1