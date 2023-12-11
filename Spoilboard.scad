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

* Mark a corner hole (X,Y zero) on the board. You will find coordinates in the output log (console) during rendering, look for "Mark the zero on spoilboard". This is important to get it right, as any error will double during production
* Align and secure a 90 degree clamp on the cnc bed. It will serve as a reference for the process
* Position the board in portrait orientation using clamp, secure it. Check that no mounting hardware intervenes with expected holes or mill head moving
* Align X,Y zero on that hole mark
* Set Z zero on the board top (controlled bty zeroZonSpoilboardSurface parameter)
* In the CAM software make sure that model's zero is preserved (it should be on the first hole)
* When preparing routes - make sure bit doesn't bump into clamps (obviously)

* Run first pass, release the board
* Turn the board 180 degrees, and secure it back the same way
* With 90 degree clamp, you should not need to change zero position
* Run the pass again

* If you were not using through holes, finish the holes with a drill slightly thicker than the threads on the bed.


If you don't have a 90 degree clamp to secure on the board, just make one! :)
Altenratively, you can mark two opposize corners on the board, and reset zero on those markings between passes. You need to be accurate in your markings. Measure thrice!



Outlining path in Autodesk Fusion if you are using drill marks:
# import STL as mesh
# Modify -> Convert mesh
# Manufacture: 
# For tool, set non-zero tip size

# Create path for chamfer: 2D pocket
## select inner large contours as Geometry
## select outer contours as Stock Contours

# path for drill marks: drill
## select centers of each mark including chamfers as points
## order points by X

Think: maybe make CNC mark the zero for the second pass

*/

publishToCommunity = false; // fast setting to use before export to GrabCad or updating GitHub renders

renderBed = false; // Use for debug and visualisation, set to false before export
renderSpoilboard = true; // set to true for export, set to false to validate spoilboard design
renderAdditionalStock = renderSpoilboard; // render additional stock under spoilboard
centerAroundFirstSpoilboardHole = true; // if true, center the fist hole
optimiseForDrilling = true;  // Set to true if you want to use drilling operation, false if you want to mill the holes out
                             // If true - you can use smaller bit with a shallow depth to create marks for manual drilling

ensureThroughHoles = !publishToCommunity && true; // WARNING: can mill into CNC bed if not careful
                // This will make the model thicker than your stock to ensure that drilling goes through thoroughly
                // Make sure to have some kind of padding or older spoilboard when running task with this parameter

turnModel =      !publishToCommunity && true; // Turn model 90 degrees for easier alignment. See instruction to see how it works
twoPassMilling = !publishToCommunity && true; // render only half of the model (split by X) for two-step marking process    
$fn =             publishToCommunity ? 36:36; // circles are rendered as regular n-gons, with n=$fn
              // lower value makes it easier to work in CAM software for post processing
              // higher value improves precision
drillingFn = 6;    // special value of fn for hole marks only. To mark drill holes, you only need a center point

zeroZonSpoilboardSurface = true;  // if set to false, the Z zero will be set on the milling bed
compensateForCircularPrecision = true;  // when using low $fn, this might be important:
    // Since circles are rendered as n-gons, their effective size is smaller than expected. This compensates for that
compensateRadiusCoefficient = compensateForCircularPrecision?1/cos(180/$fn):1;
compensateRadiusCoefficientMark = compensateForCircularPrecision?1/cos(180/drillingFn):1;


// Screw that mounts spoilboard to the bed:
screwCountersunkDepth = 3.5; // Set to 0 if don't want machined countersink or pocket at all
screwHeadWidth = 12;         // screw head diameter. If you want - add some tolerance
screwCountersunkAngle = 90;  // 90 is default for metric screws. set to 0 for straight pocket   

validateCountersunkDepth = true; // this checks that there is enough depth for the countersink
// change this value only if you understand what you are doing, the countersunk will probably render not the way you expectwant
        

spoilboardMetricThread = 6; // mm
holeDiameter = spoilboardMetricThread + 1; // allowing some wiggle room 
chamferHolesDepth = .5; // chamfer each hole to this depth. set to 0 to skip
chamferHolesAngle = screwCountersunkAngle; 

//cnc bed dimensions
bedXdimension = 360;
bedYdimension = 300;

// it's ok to use smaller spoilboard sheet, the pattern will be centered
spoilboardSheetXdimenstion = 355;
spoilboardSheetYdimenstion = 280;
// Mark the zero on spoilboard - X: 17.5 Y: 10

stockThickness = 5.9; // how thick is the spoilboard material

drillBitPointAngle = 90; // 0 for vertical holes. 
                    // Match to the mill bit tool you want to use, or to the drill bit tip.
                    // The most common included angles for drills are 118° and 135° (for hardened steel).
                    // You could use a 90-dedgree V-groove bit

// shallow markings for manual drill:
// drillBitThickness = 3;  // match to the drill bit size
limitDrillingDepth = 2; // How deep to mark holes. Ignored when ensureThroughHoles is used

drillBitThickness = 1/4 * 25.4; // One quarter bit
throughHoleToolClearance = .5; // how deep we want the tool to go under the holes to ensure clean bottom cut
cncBedClearance = 1; // how close do we want to get to the cnc bed to not ruin it

throughHoleDrillTipClearance = optimiseForDrilling? drillBitThickness/2/tan(drillBitPointAngle/2):0;
throughHoleStockClearance = (ensureThroughHoles?1:0)*(throughHoleToolClearance + throughHoleDrillTipClearance);

additionalStock = throughHoleStockClearance + (ensureThroughHoles?cncBedClearance:0);

if(additionalStock>0){
    echo(str("Ensure clearance between stock and cnc bed: ",additionalStock, " mm"));
}

// deep markings for a through drill:
spoilboardSheetThickness = stockThickness + additionalStock;

drillingDepth = ensureThroughHoles?spoilboardSheetThickness:limitDrillingDepth;
holeMaxDepth = ensureThroughHoles? spoilboardSheetThickness + cncBedClearance:stockThickness-cncBedClearance; // if you don't want through holes, limit this number to protect your bed

/*
    Here is how to use drill holes:
    1) set optimiseForDrilling = true
    2) set drillBitPointAngle
        for easiest drilling - match it to the drill tip angle or set lower
        for easiest milling - match to your working cnc bit (V-groove, probably)
    3) set drillBitThickness
        for easiest milling - match to your working bit thickness
    Note: drillingDepth is a limiting factor if your drillBitPointAngle is too sharp. 
    Rendering will prioritise drillBitPointAngle over drillBitThickness
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
    [70,108],

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

if(!supportOversizeSpoilboard){
    assert(bedXdimension>=spoilboardSheetXdimenstion, "spoilboard is too wide for X axis"); 
    assert(bedYdimension>=spoilboardSheetYdimenstion, "spoilboard is too long for Y axis");
}

if(validateCountersunkDepth && screwCountersunkDepth>0){
    assert(ensureThroughHoles || (screwCountersunkDepth <= holeMaxDepth), 
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
    

module compensateCylinder(){
    
    // cylinder(h = height, r1 = BottomRadius, r2 = TopRadius, center = true/false);
    //  cylinder(h=15, d1=20, d2=0, center=true);
    /*
    equivalent scripts
 cylinder(h=20, r=10, center=true);
 cylinder(  20,   10, 10,true);
 cylinder(  20, d=20, center=true);
 cylinder(  20,r1=10, d2=20, center=true);
 cylinder(  20,r1=10, d2=2*10, center=true);
    */
    
    
}

module RenderHoles(array, depth){
    
    counterDepth = screwCountersunkDepth;
    countersunkOuterRadius = screwHeadWidth/2;
    countersunkInnerRadius = holeDiameter/2;
    
    chamferOuterRadius = holeDiameter/2 + chamferHolesDepth*tan(chamferHolesAngle/2);
                    
    coneDepth = screwCountersunkAngle>0?
        (countersunkOuterRadius - holeDiameter/2)/tan(screwCountersunkAngle/2):counterDepth;
    
    if(screwCountersunkDepth>0){
        assert(coneDepth <= counterDepth,"Countersink hole is not deep enough for this angle");
    }
    
    cylinderDepth = counterDepth - coneDepth;
    
    holeMarkTipDepth = min(depth,drillBitPointAngle>0?min(drillingDepth,drillBitThickness/tan(drillBitPointAngle/2)/2):drillingDepth);
    holeMarkRadius = (holeMarkTipDepth)*tan(drillBitPointAngle/2);
    
    for(hole = array){
        translate([hole[0],hole[1],0]){
            
            if(optimiseForDrilling){ // render drill marks
                translate([0, 0, max(-drillingDepth,-depth)]){
                    cylinder(r1 = 0, r2 = holeMarkRadius*compensateRadiusCoefficientMark, 
                                    h = holeMarkTipDepth*1.0001, $fn=drillingFn); // tip
                
                    translate([0, 0, holeMarkTipDepth])
                            cylinder(r = holeMarkRadius*compensateRadiusCoefficientMark, 
                                     h = drillingDepth-holeMarkTipDepth+cutoutdelta/2, $fn=drillingFn); // tip
                }
                
            }else{  // render holes
                translate([0,0,-depth])
                    cylinder(d=holeDiameter*compensateRadiusCoefficient, h = depth+cutoutdelta/2);
                
                
                if(!hole[2] && chamferHolesDepth>0){ // chamfer holes
                    
                    translate([0,0,-chamferHolesDepth])
                        cylinder(r1=holeDiameter/2*compensateRadiusCoefficient, r2=chamferOuterRadius*compensateRadiusCoefficient, h = chamferHolesDepth+cutoutdelta/2);
                }

            }
            
            if(hole[2] && screwCountersunkDepth>0){ //render countersinks
                translate([0,0,-counterDepth])
                    cylinder(r1 = countersunkInnerRadius*compensateRadiusCoefficient, 
                             r2 = countersunkOuterRadius*compensateRadiusCoefficient, 
                             h = coneDepth*1.0001);
                
                if(cylinderDepth>0){
                    translate([0,0,-cylinderDepth])
                        cylinder(r=countersunkOuterRadius*compensateRadiusCoefficient, h = cylinderDepth+cutoutdelta/2);
                }
                
                if(optimiseForDrilling){
                    translate([0,0,max(-counterDepth-drillingDepth,-depth,-spoilboardSheetThickness)]) // don't sink too deep
                    {
                        cylinder(r1 = 0, r2 = holeMarkRadius*compensateRadiusCoefficientMark, 
                                            h = holeMarkTipDepth*1.0001, $fn=drillingFn); // tip
                        
                        translate([0, 0, holeMarkTipDepth])
                                cylinder(r = holeMarkRadius*compensateRadiusCoefficientMark, 
                                         h = drillingDepth-holeMarkTipDepth+cutoutdelta/2, $fn=drillingFn); // tip
                    }
                    
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
                cylinder(d=spoilboardMetricThread*compensateRadiusCoefficient, h = spoilboardSheetThickness+cutoutdelta);
        }
    }
}

module RenderSheet(){
    difference(){
        union(){
            translate([0,0,additionalStock])
                cube([twoPassMilling?spoilboardSheetXdimenstion/2:spoilboardSheetXdimenstion,
                        spoilboardSheetYdimenstion, stockThickness]);
    
            if(additionalStock>0){
                cube([twoPassMilling?spoilboardSheetXdimenstion/2:spoilboardSheetXdimenstion,
                        spoilboardSheetYdimenstion, additionalStock]);
            }
        }
        
        translate([0,0,spoilboardSheetThickness])
            RenderHoles(spoilboardHoles,min(holeMaxDepth,spoilboardSheetThickness+cutoutdelta));
    }
}


echo(str("Mark the zero on spoilboard - X: ",spoilboardHoles[0][0]," Y: ",spoilboardHoles[0][1]));
echo(str("Spoilboard corner on the bed - X: ",spoilboardXShift," Y: ",spoilboardYShift));

centerX = centerAroundFirstSpoilboardHole? spoilboardHoles[0][0] + spoilboardXShift:0;
centerY = centerAroundFirstSpoilboardHole? spoilboardHoles[0][1] + spoilboardYShift:0;

rotate([0,0,turnModel?90:0]) 
    translate([-centerX,(turnModel?-bedYdimension+centerY:-centerY),zeroZonSpoilboardSurface?-spoilboardSheetThickness:0]){    
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
