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


Note: Since OpenSCAD is limited to STL generation, and STL is not a good format for CNC milling, I'm not going to try to optimise it further and will swtich to Autodesk Fusion 360 scripting (Python)


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
* If using ensureThroughHoles - use an old spoilboard or some other material between CNC bed and new board
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

* If you were not using through holes, finish the holes with a drill slightly thicker than the threads on the bed. Try extra hard to be accurate with driles, and go in gently to prevent chipping


If you don't have a 90 degree clamp to secure on the board, just make one! :)
Altenratively, you can mark two opposize corners on the board, and reset zero on those markings between passes. You need to be accurate in your markings. Measure thrice!


Outlining path in Autodesk Fusion if you are using drill marks:
# import STL as mesh
# Go to Mesh tab
# Prepare -> Generate face groups
# Modify -> Convert mesh
# Manufacture: 
# For tool, set non-zero tip size

# Create path for chamfer: 2D pocket
## select inner large contours as Geometry
## select outer contours as Stock Contours

# path for drill marks: drill
## select centers of each mark including chamfers as points
## order points by X


Outlining path in Autodesk Fusion if you want mill to do everthing
This is super hacky, I need to get better at this stuff. Model generates with good paths, but fusion is not able to put a thick milling bit into tiny holes. So I trick it by using a 1/8 tool instead of 1/4 

# set ensureThroughHoles = true, optimizeForMilling = true, optimiseForDrilling = false
# configure the model as above
# remove extra nodes on the bottom of each hole and on the surface by doing this: enable selecting only faces, click on a face and delete it - repeat for each hole. Autodesk will get smart and "flatten" all faces on the same plane
# Then use 2D contour for all operations.
# for through holes - select small bottom circle or it's contor as geometry
# for coutnersinks and champers - use higher level contours (1 or two) as geometry

TODO: figure out how to reduce depth passes, Alternatively - how to add roughing pass easily 
*/


// 1. General Rendering configuration
    publishToCommunity = false; // fast setting to use before export to GrabCad or updating GitHub renders

    renderBed = false; // Use for debug and visualisation, set to false before export
    renderSpoilboard = true; // set to true for export, set to false to validate spoilboard design
    renderAdditionalStock = renderSpoilboard; // render additional stock under spoilboard. Change if need debugging

    centerAroundFirstSpoilboardHole = true; // if true, center the fist hole
    optimiseForDrilling = false;  // Set to true if you want to use drilling operation, false if you want to mill the holes out
                                  // If true - you can use smaller bit with a shallow depth to create marks for manual drilling

    optimizeForMilling = !publishToCommunity && true;  // creates countours for milling with V-groove bits
                                // when optimizing for milling, uses drillBitPointAngle and drillBitThickness as tool parameters
                                // can't be true if optimizeForMilling=true 

    ensureThroughHoles = !publishToCommunity && true; // WARNING: can mill into CNC bed if not careful
                    // This will make the model thicker than your stock to ensure that drilling goes through thoroughly
                    // Make sure to have some kind of padding or older spoilboard when running task with this parameter

    turnModel =      !publishToCommunity && true; // Turn model 90 degrees for easier alignment. See instruction to see how it works
    twoPassMilling = !publishToCommunity && true; // render only half of the model (split by X) for two-step marking process    
    $fn =             publishToCommunity ? 36:18; // circles are rendered as regular n-gons, with n=$fn
                  // lower value makes it easier to work in CAM software for post processing
                  // higher value improves precision
    drillingFn = optimiseForDrilling?6:$fn;    // special value of fn for drilling only. To mark drill job in CAM, you only need a center point

    zeroZonSpoilboardSurface = true;  // if set to false, the Z zero will be set on the milling bed
    compensateForCircularPrecision = true;  // when using low $fn, this might be important:
        // Since circles are rendered as n-gons, their effective size is smaller than expected. This compensates for that
        

// 2. Physical dimensions: (super important)

    //cnc bed dimensions
    bedXdimension = 360;
    bedYdimension = 300;
    bedMetricThread = 6; // mm

    // it's ok to use smaller spoilboard sheet, the pattern will be centered
    spoilboardSheetXdimenstion = 355;
    spoilboardSheetYdimenstion = 280;
    stockThickness = 5.9; // how thick is the spoilboard material

    // Screw that mounts spoilboard to the bed:
    screwCountersunkDepth = 3.5; // Set to 0 if don't want machined countersink or pocket at all
    screwHeadWidth = 12;         // screw head diameter. If you want - add some tolerance
    screwCountersunkAngle = 90;  // 90 is default for metric screws. set to 0 for straight pocket   
                                 // for best one-tool operation, ensure your working bit has the same tip angle

    validateCountersunkDepth = true; // this checks that there is enough depth for the countersink
    // change this value only if you understand what you are doing, the countersunk will probably render not the way you expect

    drillBitPointAngle = 90; // Match to the mill bit tool you want to use, or to the drill bit tip
                            // The most common included angles for drills are 118° and 135° (for hardened steel).
                            // Use a 90-dedgree V-groove bit allows you to complete the board without changing the tip
                            // Set 0 for flat end mill (180 also works)
                            // when optimising for milling, drillBitPointAngle must be equal to screwCountersunkAngle
    drillBitThickness = 1/4 * 25.4; // Drill bit thickness
    //drillBitThickness = 1/8 * 25.4;  // thinner option
    
    drillingTipDepth = (drillBitPointAngle==0 || drillBitPointAngle==180)?(optimiseForDrilling?0.1:0):drillBitThickness/tan(drillBitPointAngle/2)/2;
        // if optimiseForDrilling, non-zero height ensures a center point
    


// 3. Holes pattern:
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
        [20,20,true], // "true" marks holes used to mount Spoilboard to the bed, they will get chamfer 
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

// 4. Positioning and clearances (likely don't need to change)

    centerSpoilboard = true;   // set to false if you want to move spoilboard around the board
    // if centerSpoilboard=false, change next two variables as needed:
    spoilboardCornerX = (bedXdimension - spoilboardSheetXdimenstion)/2;     
    spoilboardCornerY = (bedYdimension - spoilboardSheetYdimenstion)/2;
    //Spoilboard corner on the bed - X: 2.5 Y: 10

    limitDrillingDepth = 2; // How deep to mark holes. Ignored when ensureThroughHoles is used

    chamferHolesDepth = .5; // chamfer each hole to this depth. set to 0 to skip
    chamferHolesAngle = drillBitPointAngle; // use the 

    holeDiameter = bedMetricThread + 1; // allowing some wiggle room. ignored when optimised for drilling
    throughHoleToolClearance = .5; // how deep we want the tool to go under the holes to ensure clean bottom cut
    cncBedClearance = 1; // protection parameter - how close do we want to get to the cnc bed to not ruin it

    spoilboardEdgeKeepOut = 6; // How close can a hole get to the edge of spoilboard for integrity 
                           // (counterink can overflow into that zone)

// End of parameters section

assert(!(optimiseForDrilling&&optimizeForMilling),"Can't optimise for drilling and milling at the same time");
assert(drillBitPointAngle >= 0 && drillBitPointAngle <= 180, "drillBitPointAngle is out of range");

assert(!optimizeForMilling || (drillBitPointAngle==screwCountersunkAngle),
                "When optimising for milling, drillBitPointAngle must be equal to screwCountersunkAngle");

throughHoleDrillTipClearance = ((optimiseForDrilling||optimizeForMilling) 
                                && (drillBitPointAngle>0&&drillBitPointAngle<180))? 
                                drillBitThickness/2/tan(drillBitPointAngle/2):0;
                                
throughHoleStockClearance = (ensureThroughHoles?1:0)*(throughHoleToolClearance + throughHoleDrillTipClearance);

additionalStock = throughHoleStockClearance + (ensureThroughHoles?cncBedClearance:0);
if(additionalStock>0){
    echo(str("Ensure clearance between stock and cnc bed: ",additionalStock, " mm"));
}

spoilboardSheetThickness = stockThickness + additionalStock;

drillingDepth = ensureThroughHoles ? spoilboardSheetThickness:limitDrillingDepth;
holeMaxDepth = (ensureThroughHoles ? spoilboardSheetThickness:stockThickness) - cncBedClearance; 

compensateRadiusCoefficient = compensateForCircularPrecision?1/cos(180/$fn):1;
compensateRadiusCoefficientMark = compensateForCircularPrecision?1/cos(180/drillingFn):1;

// Technical parameters, not important
cutoutdelta=.1;// eny positive number should work
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
    

module drillingHole(maxDepth, maxRadius = 0){
    // cylinder ending with a cone, summing together up to drillingDepth
    
    // optimise for milling - ensure there is a contour for the tool tip to follow easily
    // consider 1/4 and 1/8 width for the tool
    
    // break down cones to allow one path by the tool
    // problem: 1/4 inch tool might be too bif for the chamfer
    // problem: openSCAD might weld cones together. Consider minor adjustment
                
    drillingDiameter = optimiseForDrilling ? drillBitThickness: holeDiameter;
    drillingRadius = (maxRadius>0) ? min(drillingDiameter/2, maxRadius) : (drillingDiameter/2);
    
    drillingTipRadius = (drillingDiameter-drillBitThickness)/2; // will be 0 if optimised for drilling    
    // drillingDepth calculated before
   
    translate([0, 0, max(-drillingDepth,-maxDepth)]){
        if(drillingTipDepth > 0){
            cylinder(r1 = drillingTipRadius, r2 = drillingRadius*compensateRadiusCoefficientMark, 
                      h = drillingTipDepth, $fn=drillingFn); // tip
            // ARTIFACTS HERE
        }
    
        if(drillingDepth > drillingTipDepth){
            translate([0, 0, drillingTipDepth])
                cylinder(r = drillingRadius*compensateRadiusCoefficientMark, 
                         h = drillingDepth-drillingTipDepth+cutoutdelta/2, $fn=drillingFn); // tip
        }
    }
    
}

module RenderHoles(array, depth){
    
    counterDepth = screwCountersunkDepth;
    countersunkOuterRadius = screwHeadWidth/2;
    countersunkInnerRadius = holeDiameter/2;
    
    chamferOuterRadius = holeDiameter/2 + chamferHolesDepth*tan(chamferHolesAngle/2);
                    
    coneDepth = screwCountersunkAngle>0?
        (countersunkOuterRadius - holeDiameter/2)/tan(screwCountersunkAngle/2):0;
    
    if(screwCountersunkDepth>0){
        assert(coneDepth <= counterDepth,"Countersink hole is not deep enough for this angle");
    }
    
    cylinderDepth = counterDepth - coneDepth;
    
    optimiseConeForMilling = !(!optimizeForMilling || drillingTipDepth==0 || coneDepth/drillingTipDepth>2);
    if(!optimiseConeForMilling && optimizeForMilling){
        echo("can't optimise countersink for milling with flat drill bit, or countersink is too deep");
    }
    
    // three levels: countersunkInnerRadius, countersunkMidRadius, countersunkOuterRadius
    //               -counterDepth-coneDepth  -drillingTipDepth
    midDepth = drillingTipDepth;
    countersunkMidRadius = countersunkOuterRadius - drillBitThickness/2;
    //countersunkInnerRadius + (countersunkOuterRadius - countersunkInnerRadius) * (coneDepth - drillingTipDepth)/coneDepth;
    echo("radius",countersunkMidRadius,countersunkInnerRadius);
                    
    
    for(hole = array){
        translate([hole[0],hole[1],0]){
            
            if(optimiseForDrilling || optimizeForMilling){ // render drill marks
                if(!hole[2]){
                    drillingHole(depth);
                }
            }else{  // render holes
                translate([0,0,-depth])
                    cylinder(d=holeDiameter*compensateRadiusCoefficient, h = depth+cutoutdelta/2);
            }
            if(!optimiseForDrilling && !hole[2] && chamferHolesDepth>0){ // chamfer for mounting screws
                translate([0,0,-chamferHolesDepth])
                    cylinder(r1=holeDiameter/2*compensateRadiusCoefficient, r2=chamferOuterRadius*compensateRadiusCoefficient, h = chamferHolesDepth+cutoutdelta/2);
            }
            // render countersinks:
            if(hole[2] && screwCountersunkDepth>0){ 
                if(!optimiseConeForMilling){
                    translate([0,0,-counterDepth]){
                        cylinder(r1 = countersunkInnerRadius*compensateRadiusCoefficient, 
                                 r2 = countersunkOuterRadius*compensateRadiusCoefficient, 
                                 h = coneDepth);             // ARTIFACTS HERE
                    } 
                }else{
                    translate([0,0,-counterDepth + (coneDepth-midDepth)]){
                        cylinder(r1 = countersunkMidRadius*compensateRadiusCoefficient, 
                             r2 = countersunkOuterRadius*compensateRadiusCoefficient, 
                             h = midDepth);            // ARTIFACTS HERE
                    }
                    
                    if(coneDepth > midDepth){ // Actually need more layers
                        translate([0,0,-counterDepth]){ // deeper
                            cylinder(r1 = countersunkInnerRadius*compensateRadiusCoefficient, 
                                 r2 = countersunkMidRadius*compensateRadiusCoefficient, 
                                 h = (coneDepth-midDepth));             // ARTIFACTS HERE
                        }
                    }
                }
                
                if(cylinderDepth>0){
                    translate([0,0,-cylinderDepth])
                        cylinder(r=countersunkOuterRadius*compensateRadiusCoefficient, h = cylinderDepth+cutoutdelta/2);
                }
                
                if(optimiseForDrilling || optimizeForMilling){ // render drill marks
                    drillingHole(min(counterDepth+drillingDepth,depth,spoilboardSheetThickness), 
                                    optimizeForMilling?countersunkMidRadius:0);
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
                cylinder(d=bedMetricThread*compensateRadiusCoefficient, h = spoilboardSheetThickness+cutoutdelta);
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
