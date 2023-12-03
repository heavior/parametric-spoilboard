# Parametric OpenSCAD model for generating CNC spoilboards

This file is for generating spoilboards for CNC that have flat beds with grids of holes instead of slots

DIY spoilboard is cheaper and can be tuned to your needs. You can:
* use thinner spoilboard to save some vertical height
* choose alternatives to MDF such as plywood or plastic
* customise board size for a specific job
* position on the CNC bed as you want

This design relies on original threaded holes on the CNC bed for mounting, it does not use threaded incerts in the  sheet. If you prefer threaded incerts, modify the code as you need.

How to use:
1) Configure holes and other parameters at the beginning of the file
2) Export STL
3) Use you preferred CAD software to create G-code
4) Use your CNC to prepare the board

Two options for how to do it:
* Make CNC do all the work
* Use CNC to mark the grid, and then complete the job with a drill
Either option works well, because through holes do not require absolute precision.

Default values here are for Genmitsu 3030-Pro, but you can tweak it as you wish. Please, share grid patterns for other CNC mills.

# Available renders:
If you want quick access to the STL files, and don't want to play with OpenSCAD, check out these renders.
Please note that your might have an MDF board with different dimensions, different screws and otherwise different preferences, and you might have to tune the models in your favoride CAD software. I'd recommend tuning everything in OpenSCAD

renders/3030-cncbed.stl - 3D model of Sainsmart Genmitsu 3030-pro cnc mill
renders/3030-spoilboard-through.stl - 3D model of a spoilboard with through holes and countersink
renders/3030-spoilboard-drill.stl - 3D model with only drill marks for all the holes

# Contributions
If you find this model useful, and you have traced a hole pattern from a different cnc model, please consider sharing the new configuration back to the community.

# Links
Also available in Grabcad community: https://grabcad.com/library/parametric-spoilboard-and-pattern-for-genmitsu-sainsmart-3030-pro-cnc-1