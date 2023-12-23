"""
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
"""

"""
# Parametric Autodesk Fusion model for generating CNC spoilboards and Sainsmart Genmitsu 3030-Pro cnc bed grid pattern

Readme file with more details available here: https://github.com/heavior/parametric-spoilboard

How to use:
1) Configure holes and other parameters at the beginning of the file
2) Run script in Autodesk Fusion 360
3) Set up manufacturing: drill or bore the hole, then chamfer edges
4) Use your CNC to prepare the board

Manufacturing:

If you are maximizing spoilboard size, your CNC x/y range is likely not wide enough to make the model in one pass, and you will need two runs.

Instruction for Genmitsu 3030-Pro (for other CNC mills, read this and get creative): 
* Set turnModel = true , it will turn the model to make it easier to prepare for milling
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

"""


import adsk.core, adsk.fusion, adsk.cam, traceback
import math


exceptionUICounter = 0 
maxExceptions = 4 # script will not show more exceptions than this

# 1. General Rendering configuration
publishToCommunity = True # fast setting to use before export to GrabCad or updating GitHub renders

renderBed = False       # Use for debug and visualisation
renderSpoilboard = True # set to true for machinning, set to false to validate spoilboard design
renderAdditionalStock = False # renderSpoilboard    # render additional stock under spoilboard. Change if need debugging
# TODO: test addional stock in fusion

ensureThroughHoles = not publishToCommunity and True  # WARNING: can mill into CNC bed if not careful
                            # This will make the model thicker than your stock to ensure that milling goes through thoroughly
                            # Make sure to have some kind of padding or older spoilboard when running task with this parameter

turnModel =      not publishToCommunity and True    # Turn model 90 degrees for easier alignment. See instruction to see how it works
twoPassMilling = not publishToCommunity and True    # render only half of the model (split by X) for two-step marking process    

cleanModel =     not publishToCommunity and False    # script will remove objects and stetches from the project - simplifies script debug

# 2. Physical dimensions: (super important)
# bed dimensions
bedXdimension = 360
bedYdimension = 300
bedMetricThread = 6 # mm

# it's ok to use smaller spoilboard sheet, the pattern will be centered
spoilboardSheetXdimenstion = 355
spoilboardSheetYdimenstion = 280
stockThickness = 5.9 # how thick is the spoilboard material

# Screw that mounts spoilboard to the bed:
screwCountersunkDepth = 3.5 # Set to 0 if don't want machined countersink or pocket at all
screwHeadWidth = 12         # screw head diameter. If you want - add some tolerance
screwCountersunkAngle = 90  # 90 is default for metric screws. set to 0 for straight pocket   
                                # for best one-tool operation, ensure your working bit has the same tip angle

validateCountersunkDepth = True # this checks that there is enough depth for the countersink
# change this value only if you understand what you are doing, the countersunk will probably render not the way you expect

millBitPointAngle = 90 # Match to the mill bit tool you want to use, or to the mill bit tip
                            # The most common included angles for mills are 118° and 135° (for hardened steel).
                            # Use a 90-dedgree V-groove bit allows you to complete the board without changing the tip
                            # Set 0 for flat end mill (180 also works)
                            # when optimising for milling, millBitPointAngle must be equal to screwCountersunkAngle
millBitThickness = 1/4 * 25.4 # mill bit thickness
#millBitThickness = 1/8 * 25.4  # thinner option    

# 3. Holes pattern:
# cnc beds have irregular hole patterns, but tend to be symmetrical. 
# This allows us to set hole pattern only for one corner, and script will calculate 
boardXsymmetrical = True 
boardYsymmetrical = True

# Now go through the holes on not symmetrical and set up
# [X,Y,mount] hole _centers_ measured from the edge of cnc bed
# try to be within 1mm precision
# third parameter is true or false. true if it will be used to secure Spoilboard on the bed
holes = [
    #row 1
        [20, 20, True], # "true" marks holes used to mount Spoilboard to the bed, they will get chamfer 
        [80, 20, False],
        [140, 20, False],

    #row 2
        [50, 45, False],
        [110, 45, False],

    #row 3
        [20, 70, False],
        [80, 70, False],
        [140, 70, False],

    #row 4
        [110, 97.5, False],

    #row 5
        [70, 108, False],

    #row 6
        [20, 125, False],
        [140, 125, False],

    #row 7
        [70, bedYdimension/2, False],
        [110, bedYdimension/2, False],
]
# 4. Positioning and clearances (likely don't need to change)

centerSpoilboard = True   # set to false if you want to move spoilboard around the board
# if centerSpoilboard=false, change next two variables as needed:
spoilboardCornerX = (bedXdimension - spoilboardSheetXdimenstion)/2     
spoilboardCornerY = (bedYdimension - spoilboardSheetYdimenstion)/2
#Spoilboard corner on the bed - X: 2.5 Y: 10

limitMillingDepth = 5 # How deep to mill holes. Ignored when ensureThroughHoles is used

chamferWidth = .5 # chamfer for each hole 
chamferHolesAngle = millBitPointAngle 

holeDiameter = bedMetricThread + 1 # allowing some wiggle room. ignored when optimised for milling
throughHoleToolClearance = .5 # how deep we want the tool to go under the holes to ensure clean bottom cut
cncBedClearance = 1 # protection parameter - how close do we want to get to the cnc bed to not ruin it

spoilboardEdgeKeepOut = 6 # How close can a hole get to the edge of spoilboard for integrity 
                        # (counterink can overflow into that zone)


# Access to the application and root component
app = adsk.core.Application.get()
ui = app.userInterface
rootComp = app.activeProduct.rootComponent

def toCM(value):
    return value/10.0;

def createMMValue(value):
    # TODO: confirm this
    return adsk.core.ValueInput.createByReal(toCM(value))

def createDegValue(degrees):
    # Create a ValueInput for a value in degrees
    return adsk.core.ValueInput.createByString(f"{degrees} deg")


def deleteAllBodiesAndSketches():
    # Delete all bodies
    while rootComp.bRepBodies.count > 0:
        body = rootComp.bRepBodies.item(0)
        body.deleteMe()

    # Delete all sketches
    while rootComp.sketches.count > 0:
        sketch = rootComp.sketches.item(0)
        sketch.deleteMe()


def renderBox(name, sizeX, sizeY, sizeZ, cornerX, cornerY, cornerZ):
    # Create a new sketch on the xy plane for the box
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    boxSketch = sketches.add(xyPlane)

    # Draw a rectangle on the sketch for the box
    lines = boxSketch.sketchCurves.sketchLines
    rect = lines.addTwoPointRectangle(adsk.core.Point3D.create(toCM(cornerX), toCM(cornerY), toCM(cornerZ)),
                                      adsk.core.Point3D.create(toCM(cornerX + sizeX), toCM(cornerY + sizeY), toCM(cornerZ)))

    # Extrude the sketch to create the box
    prof = boxSketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

    # Define the distance for the extrusion
    distance = createMMValue(sizeZ)
    extInput.setDistanceExtent(False, distance)

    # Create the box
    box = extrudes.add(extInput)

    # Delete the sketch
    boxSketch.deleteMe()

    # Set name
    if box.bodies.count == 0:
        raise Exception('No body was created by the extrusion.')
    body = box.bodies.item(0)
    body.name = name
    return body

def createSketchWithPoints(name, component, points, plane, mountingHoles, shiftX, shiftY):
    # Create a new sketch on the specified plane
    sketches = component.sketches
    sketch = sketches.add(plane)
    sketch.name = name
    # collection = adsk.core.ObjectCollection.create()
    # Iterate over the points array and add them to the sketch
    for point in points:
        x, y, mounting = point  # Extract x and y coordinates
        if mounting == mountingHoles:
            sketchPoint = adsk.core.Point3D.create(toCM(x + shiftX), toCM(y + shiftY), 0)  # Create a Fusion 360 point
            sketch.sketchPoints.add(sketchPoint)  # Add the point to the sketchtoCM(
            # collection.add(sketchPoint)
    sketch.sketchPoints.item(0).deleteMe()
    return sketch


def getSketchPointCoordinates(sketchPoint):
    pointGeometry = sketchPoint.geometry
    x = pointGeometry.x
    y = pointGeometry.y
    return f"({x}, {y})"

def createHolesFromSketch(targetBody, points, diameter, depth, countersinkDiameter=0, countersinkAngle=0, drillTipAngle=0):
    # Iterate through all sketch points and create holes
    holes = rootComp.features.holeFeatures

    #skipFirst = True # hack to avoud first point on the sketch - zero,zero
    #points.sketchPoints.item(0).deleteMe()
    collection = adsk.core.ObjectCollection.create()
    for sketchPoint in points.sketchPoints:
        collection.add(sketchPoint)
        
    try:
        if countersinkAngle:
            #raise Exception("createCountersinkInput {},{},{} ".format(diameter, countersinkDiameter, countersinkAngle))
            holeInput = holes.createCountersinkInput(createMMValue(diameter), createMMValue(countersinkDiameter), createDegValue(countersinkAngle))
        elif countersinkDiameter: # TODO: support counterbore depth
            #raise Exception("createCounterboreInput {},{},{} ".format(diameter, countersinkDiameter, (countersinkDiameter - diameter)/2))
            holeInput = holes.createCounterboreInput(createMMValue(diameter), createMMValue(countersinkDiameter), createMMValue((countersinkDiameter - diameter)/2))
        else:
            holeInput = holes.createSimpleInput(createMMValue(diameter))

        holeInput.participantBodies = [targetBody]

        holeInput.setPositionBySketchPoints(collection)
        holeInput.setDistanceExtent(createMMValue(depth))

        if drillTipAngle:
            holeInput.tipAngle = createDegValue(drillTipAngle)        
        hole = holes.add(holeInput)
        return
    except:
        global exceptionUICounter
        if exceptionUICounter < maxExceptions and ui:
            ui.messageBox('Failed to create hole at point {}:\n{}'.format(getSketchPointCoordinates(sketchPoint),traceback.format_exc()))            
        exceptionUICounter += 1

def run(context):
    global holes, bedXdimension, bedYdimension, spoilboardSheetXdimenstion, spoilboardSheetYdimenstion
    # parameter validation and some prep calculations:
    # check parameters

    millingTipDepth = 0 if (millBitPointAngle==0 or millBitPointAngle==180) else millBitThickness/math.tan(millBitPointAngle/2 * math.pi/2)/2
    throughHoleStockClearance = (throughHoleToolClearance + millingTipDepth) if ensureThroughHoles else 0
    additionalStock = throughHoleStockClearance + (cncBedClearance if ensureThroughHoles else 0)
                                                
    # if additionalStock > 0:
    #    print ("Ensure clearance between stock and cnc bed: " + str(additionalStock) + " mm")

    spoilboardSheetThickness = stockThickness + (additionalStock if renderAdditionalStock else 0)
    millingDepth = spoilboardSheetThickness if ensureThroughHoles else limitMillingDepth
    holeMaxDepth = (spoilboardSheetThickness + additionalStock if ensureThroughHoles else stockThickness) - cncBedClearance 

    supportOversizeSpoilboard = False # this checks that Spoilboard sheet is smaller than the board. 
                                      # change this value only if you understand what you are doing

    if not supportOversizeSpoilboard:
        assert bedXdimension >= spoilboardSheetXdimenstion, "spoilboard is too wide for X axis"
        assert bedYdimension >= spoilboardSheetYdimenstion, "spoilboard is too long for Y axis"
    if validateCountersunkDepth and screwCountersunkDepth>0:
        assert ensureThroughHoles or (screwCountersunkDepth <= holeMaxDepth), "max hole depth is not deep enough for countrsunk, min holeMaxDepth: " + str(screwCountersunkDepth)
        assert screwCountersunkAngle >= 0 and screwCountersunkAngle <= 180, "screwCountersunkAngle is out of range"        
        if screwCountersunkAngle > 0:
            requiredCounterSunkDepth = (screwHeadWidth - holeDiameter)/2/ math.tan(screwCountersunkAngle/2 * math.pi/2)/2
            assert requiredCounterSunkDepth <= screwCountersunkDepth, "countersunk is too shallow for this angle, min screwCountersunkDepth: " + str(requiredCounterSunkDepth)

    # Completing holes array with symmetrical values
    if boardXsymmetrical:
        holes += [[bedXdimension - elem[0], elem[1], elem[2]] for elem in holes]

    if boardYsymmetrical:
        holes += [[elem[0], bedYdimension - elem[1], elem[2]] for elem in holes]

    def remove_duplicate_holes(holes):
        unique_holes = set()
        cleaned_holes = []

        for hole in holes:
            # Convert the list to a tuple for hashing
            hole_tuple = tuple(hole)
            if hole_tuple not in unique_holes:
                unique_holes.add(hole_tuple)
                cleaned_holes.append(hole)

        return cleaned_holes

    spoilboardXShift = (bedXdimension - spoilboardSheetXdimenstion) / 2 if centerSpoilboard else spoilboardCornerX
    spoilboardYShift = (bedYdimension - spoilboardSheetYdimenstion) / 2 if centerSpoilboard else spoilboardCornerY

    # here we realign all holes to the spoilboard system of coordinates
    # TODO: this is not important for autodesk, so it can be optimised to use global coordinates
    spoilboardHoles = [[elem[0] - spoilboardXShift, elem[1] - spoilboardYShift, elem[2]] for elem in remove_duplicate_holes(holes)]

    realKeepout = spoilboardEdgeKeepOut + holeDiameter/2

    def spoilboardHoleCheck(hole):
        return hole[0] >= realKeepout and hole[1] >= realKeepout and hole[0] <= spoilboardSheetXdimenstion - realKeepout and hole[1] <= spoilboardSheetYdimenstion - realKeepout    
        
    spoilboardHoles = [elem for elem in spoilboardHoles if spoilboardHoleCheck(elem)]

    # now we have an array that's ready to use, let's get to rendering

    # getting the coordinates that should be 0,0 - aligning on the first hole
    centerX = spoilboardHoles[0][0];
    centerY = spoilboardHoles[0][1];

    if twoPassMilling: # just cut the board in half, at this point we don't need original dimensions anymore
        spoilboardSheetXdimenstion = spoilboardSheetXdimenstion/2

    if turnModel:  # to turn model - swap X and Y everywhere
        (centerX, centerY) = (centerY, centerX) 
        (bedXdimension, bedYdimension) = (bedYdimension, bedXdimension)
        (spoilboardSheetXdimenstion, spoilboardSheetYdimenstion) = (spoilboardSheetYdimenstion, spoilboardSheetXdimenstion)
        (spoilboardXShift, spoilboardYShift) =  (spoilboardYShift, spoilboardXShift)
        for hole in spoilboardHoles:
            (hole[0], hole[1]) = (hole[1], hole[0])
        
    try:
        if cleanModel:
            deleteAllBodiesAndSketches()

        xyPlane = rootComp.xYConstructionPlane
        mountingHoleCollection = createSketchWithPoints("Mounting points", rootComp, spoilboardHoles, xyPlane, True,  -centerX, -centerY)
        holeCollection = createSketchWithPoints("Drilling points", rootComp, spoilboardHoles, xyPlane, False, -centerX, -centerY)
        
        if renderBed:
            bed = renderBox("CNC bed", bedXdimension, bedYdimension, spoilboardSheetThickness, -centerX-spoilboardXShift, -centerY-spoilboardYShift, -2*spoilboardSheetThickness);
            createHolesFromSketch(bed,mountingHoleCollection, bedMetricThread, 2*spoilboardSheetThickness, 0, 0, 0)
            createHolesFromSketch(bed,holeCollection, bedMetricThread, 2*spoilboardSheetThickness, 0, 0, 0)

        if renderSpoilboard:
            spoilboard = renderBox("Spoilboard", spoilboardSheetXdimenstion, spoilboardSheetYdimenstion, spoilboardSheetThickness, -centerX, -centerY, -spoilboardSheetThickness);
            createHolesFromSketch(spoilboard,mountingHoleCollection, holeDiameter, holeMaxDepth, screwHeadWidth, screwCountersunkAngle, millBitPointAngle)
            createHolesFromSketch(spoilboard,holeCollection, holeDiameter, holeMaxDepth, holeDiameter + 2*chamferWidth, chamferHolesAngle, millBitPointAngle)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
