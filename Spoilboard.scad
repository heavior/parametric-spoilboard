/*
For this file only:

MIT License

Copyright (c) 2023  Evgeny Balashov https://www.linkedin.com/in/balashovevgeny/
Original source and latest versions: https://github.com/heavior/parametric-spoilboard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

/*
# Parametric OpenSCAD model for generating CNC spoilboards and Sainsmart Genmitsu 3030-Pro cnc bed grid pattern

Readme file with more details available here: https://github.com/heavior/parametric-spoilboard

How to use:
1) Configure holes and other parameters at the beginning of the file
2) Export STL
3) Use you preferred CAD software to create G-code
4) Use your CNC to prepare the board

Manufacturing:

If you are maximizing spoilboard size, your CNC x/y range is likely not wide enough to make the model in one pass, and you will need two runs.

Instruction for Genmitsu 3030-Pro (for other CNC mills, read this and get creative): 
* Set turnModel = true , it will turn the model to make it easier to prepare in CAM
* Set twoPassMilling = true, it will optimise the render for a two-pass milling
* Mark two opposite coner holes on the board with a sharp object. You will find coordinates in the output log (console) during rendering, look for "Mark the zero on spoilboard"
* Validate the disance between markings. It is important to get it right
* Secure the board on the cnc bed in portrait orientation, you will have side holes available for stock clamps. Make sure to not clamp where some other hole is expected to be
* Align X,Y zero on that hole mark, set Z zero on the bed level (positive Z is expected to look up from the bed)
* In the CAM software make sure that model's zero is preserved (it should be on the first hole)
* When preparing routes - make sure bit doesn't bump into clamps (obviously)

* Run first pass, release the board
* Finish the holes (drill if needed)
* Flip the board, secure it using freshly made holes
* Realign X,Y zero with the opposite corner
* Run the pass again

TODO: make CNC mark the zero for the second pass

*/

renderBed = true; // Use for debug and visualisation, set to false before export
renderSpoilboard = true; // set to true for export, set to false to validate spoilboard design
centerAroundFirstSpoilboardHole = true; // if true, center the fist hole
turnModel = true; // Turn model 90 degrees for easier alignment. See instruction to see how it works
twoPassMilling = true; // render only half of the model (split by X) for two-step marking process

markDrillHoles = true;  // Set to true if you want hole marks for drill, false if you want CNC to complete the holes

// Screw that mounts spoilboard to the bed:
screwCountersunkDepth = 4.5; // Set to 0 if don't want machined countersink or pocket at all
screwHeadWidth = 11;         // screw head diameter. If you want - add some tolerance
screwCountersunkAngle = 90;  // 90 is default for metric screws. set to 0 for straight pocket   

validateCountersunkDepth = true; // this checks that there is enough depth for the countersink
// change this value only if you understand what you are doing, the countersunk will probably render not the way you expectwant
        
spoilboardMetricThread = 6; // mm
holeDiameter = spoilboardMetricThread + .5; // allowing some wiggle room 

//cnc bed dimensions 
bedXdimension = 360;
bedYdimension = 300;

// it's ok to use smaller spoilboard sheet, the pattern will be centered
spoilboardSheetXdimenstion = 355;
// Mark the zero on spoilboard - X: 17.5 Y: 10
spoilboardSheetYdimenstion = 280;
spoilboardSheetThickness = 5.9;
holeMaxDepth = spoilboardSheetThickness + 2; // if you don't want through holes, limit this number to protect your bed
holeDefaultDepth = holeMaxDepth;

holeMarkAngle = 90; // 0 for vertical holes
holeMarkWidth = 2;
holeMarkDepth = 4.5;
/*
    Here is how to use drill holes:
    1) set markDrillHoles = true
    2) set holeMarkAngle
        for easiest drilling - match it to the drill tip angle or set lower
        for easiest milling - match to your working cnc bit (V-groove, probably)
    3) set holeMarkWidth
        for easiest milling - match to your working bit thickness
    Note: holeMarkDepth is a limiting factor if your holeMarkAngle is too sharp. 
    Rendering will prioritise holeMarkAngle over holeMarkWidth
*/

                    
spoilboardEdgeKeepOut = 6; // How close can a hole get to the edge of spoilboard for integrity (counterink can overflow into that zone)
centerSpoilboard = true;   // set to false if you want to move spoilboard around the board
// if centerSpoilboard=false, change next two variables as needed:
spoilboardCornerX = (bedXdimension - spoilboardSheetXdimenstion)/2;     
spoilboardCornerY = (bedYdimension - spoilboardSheetYdimenstion)/2;
//Spoilboard corner on the bed - X: 2.5 Y: 10


// cnc beds have irregular hole patterns, but tend to be symmetrical. 
// This allows us to set hole pattern only for one corner, and script will calculate 
boardXsymmetrical = true; 
boardYsymmetrical = true;

// Now go through the holes on not symmetrical and set up
// [X,Y,mount] hole _centers_ measured from the edge of cnc bed
// try to be within 1mm precision
// third parameter is true or false. true if it will be used to secure Spoilboard on the bed
holes = [
//row 1
    [20,20,true], // true marks holes used to mount Spoilboard to the bed, they will get shapmher 
    [80,20],
    [140,20],

//row 2
    [50,45],
    [110,45],

//row 3
    [20,70],
    [80,70],
    [140,70],

//row 4
    [110,97.5],

//row 5
    [70,100.8],

//row 6
    [20,125],
    [140,125],

//row 7
    [70,bedYdimension/2],
    [110,bedYdimension/2],

];



// Technical parameters, not important
cutoutdelta=1;// eny positive number shouldwork
supportOversizeSpoilboard = false; // this checks that Spoilboard sheet is smaller than the board. 
                                   // change this value only if you understand what you are doing

// OpenSCAD precision settings for circles
// $fs is a surface size. mark holes will have a problem with this value
// $fa is angle
// $fn is number for each circle
// lower values will create more surfaces in STL and higher precision, but it can drive your CAD software crazy with too many triangles
/*
$fs = .2;
$fa = 1;
*/
$fn = 20;

if(!supportOversizeSpoilboard){
    assert(bedXdimension>=spoilboardSheetXdimenstion, "spoilboard is too wide for X axis"); 
    assert(bedYdimension>=spoilboardSheetYdimenstion, "spoilboard is too long for Y axis");
}

if(validateCountersunkDepth && screwCountersunkDepth>0){
    assert(screwCountersunkDepth <= holeMaxDepth, 
        str("max hole depth is not deep enough for countrsunk, min holeMaxDepth: ", screwCountersunkDepth));
    assert(screwCountersunkAngle >= 0, "negative countersunk angle");
    assert(screwCountersunkAngle < 180, "countersunk angle is too large");
    //assert(screwCountersunkAngle <= 90, "countersunk angle above 90 is not supported yet");
    
    if(screwCountersunkAngle > 0){
        requiredCounterSunkDepth = (screwHeadWidth - holeDiameter)/2/tan(screwCountersunkAngle/2);
        assert(requiredCounterSunkDepth <= screwCountersunkDepth, str("countersunk is too shallow for this angle, min screwCountersunkDepth: ",requiredCounterSunkDepth));
    }
}

// completing holes array with symmetrical values
holes2 = [
    for (elem = holes) elem,
    if(boardXsymmetrical) for (elem = holes) [ bedXdimension-elem[0], elem[1], elem[2]]
];
bedHoles = [
    for (elem = holes2) elem,
    if(boardYsymmetrical) for (elem = holes2) [ elem[0], bedYdimension-elem[1], elem[2]]
];



spoilboardXShift = centerSpoilboard?(bedXdimension - spoilboardSheetXdimenstion)/2:spoilboardCornerX;
spoilboardYShift = centerSpoilboard?(bedYdimension - spoilboardSheetYdimenstion)/2:spoilboardCornerY;
spoilboardHolesRaw = [ for (elem = bedHoles) [elem[0] - spoilboardXShift,elem[1] - spoilboardYShift, elem[2]]];
    
realKeepout = spoilboardEdgeKeepOut + holeDiameter/2;
function spoilboardHoleCheck(hole) = 
    hole[0] >= realKeepout 
    && hole[1] >= realKeepout 
    && hole[0] <= spoilboardSheetXdimenstion - realKeepout 
    && hole[1] <= spoilboardSheetYdimenstion - realKeepout;    
spoilboardHoles = [ for (elem = spoilboardHolesRaw) if(spoilboardHoleCheck(elem)) elem]; // remove holes that are too close to the edge
    


module RenderHoles(array, depth){
    
    counterDepth = screwCountersunkDepth;
    countersunkOuterRadius = screwHeadWidth/2;
    countersunkInnerRadius = holeDiameter/2;
    coneDepth = screwCountersunkAngle>0?
        (countersunkOuterRadius - holeDiameter/2)/tan(screwCountersunkAngle/2):counterDepth;
    
    if(screwCountersunkDepth>0){
        assert(coneDepth <= counterDepth,"Countersink hole is not deep enough for this angle");
    }
    
    cylinderDepth = counterDepth - coneDepth;
    
    holeMarkRealDepth = min(depth,holeMarkAngle>0?min(holeMarkDepth,holeMarkWidth/tan(holeMarkAngle/2)/2):holeMarkDepth);
    holeMarkRadius = (holeMarkRealDepth+cutoutdelta/2)*tan(holeMarkAngle/2);
    
    for(hole = array){
        translate([hole[0],hole[1],0]){
            
            if(markDrillHoles){ // render drill marks
                translate([0,0,-holeMarkRealDepth])
                    cylinder(r1 = 0, r2 = holeMarkRadius, h = holeMarkRealDepth+cutoutdelta/2);
                
            }else{  // render holes
                translate([0,0,-depth])
                    cylinder(d=holeDiameter, h = depth+cutoutdelta/2);
            }
            
            if(hole[2] && screwCountersunkDepth>0){ //render countersinks
                translate([0,0,-counterDepth])
                    cylinder(r1 = countersunkInnerRadius, 
                             r2 = countersunkOuterRadius, 
                             h = coneDepth*1.0001);
                
                if(cylinderDepth>0){
                    translate([0,0,-cylinderDepth])
                        cylinder(r=countersunkOuterRadius, h = cylinderDepth+cutoutdelta/2);
                }
                
                if(markDrillHoles){
                    translate([0,0,max(-counterDepth-holeMarkRealDepth,-depth)]) // don't sink too deep
                        cylinder(r1 = 0, r2 = holeMarkRadius, h = holeMarkRealDepth+cutoutdelta/2);
                }
            }
        }
    }
}

module RenderBed(){
    difference(){
        cube([bedXdimension,bedYdimension,spoilboardSheetThickness]);
         for(hole = bedHoles){
            translate([hole[0],hole[1],-cutoutdelta/2])
                cylinder(d=spoilboardMetricThread, h = spoilboardSheetThickness+cutoutdelta);
        }
    }
}

module RenderSheet(){
    difference(){
        cube([twoPassMilling?spoilboardSheetXdimenstion/2:spoilboardSheetXdimenstion,spoilboardSheetYdimenstion,spoilboardSheetThickness]);
        translate([0,0,spoilboardSheetThickness])
            RenderHoles(spoilboardHoles,min(holeMaxDepth,spoilboardSheetThickness+cutoutdelta));
    }
}


echo(str("Mark the zero on spoilboard - X: ",spoilboardHoles[0][0]," Y: ",spoilboardHoles[0][1]));

echo(str("Spoilboard corner on the bed - X: ",spoilboardXShift," Y: ",spoilboardYShift));

centerX = centerAroundFirstSpoilboardHole? spoilboardHoles[0][0] + spoilboardXShift:0;
centerY = centerAroundFirstSpoilboardHole? spoilboardHoles[0][1] + spoilboardYShift:0;

rotate([0,0,turnModel?90:0]) 
    translate([-centerX,(turnModel?-bedYdimension+centerY:-centerY),0]){    
        if(renderBed){
            color("gray")
            translate([0,0,-spoilboardSheetThickness])
                RenderBed();
        }
        if(renderSpoilboard){
            translate([spoilboardXShift,spoilboardYShift,0]){
                RenderSheet();   
            }
        }
    }
