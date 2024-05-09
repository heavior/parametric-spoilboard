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

* Mark a corner hole (X,Y zero) on the board. You will see coordinates on the pop-up message "Mark the zero on spoilboard".

> Note: At first I tried to use corner hole, but after multiple tests I realised that it's very hard to get it right: any mistake doubles and pattern gets too wide or too narrow
> New approach allows validation of center hole for the second pass. Zero point will be not the corner, but the left most hole in the center row.
> The pass will not not only drill through holes for the first pass, but also it will do a shallow drilling to mark the next zero point  

* If using ensureThroughHoles - use an old spoilboard or some other material between CNC bed and new board
* Align and secure a 90 degree clamp on the cnc bed. It will serve as a reference for the process
* Position the board in portrait orientation using clamp, secure it. Check that no mounting hardware intervenes with expected holes or mill head moving
* Align X,Y zero on that hole mark
* Set Z zero on the board top (controlled bty zeroZonSpoilboardSurface parameter)
* In the CAM software make sure that model's zero is preserved (it should be on the first hole)
* When preparing routes - make sure bit doesn't bump into clamps (obviously)

* Run first pass, release the board
* Turn the board 180 degrees, and secure it back the same way
# Tune zero point, it should be close to the original, but might move
* Run the pass again

* If you were not using through holes, finish the holes with a drill slightly thicker than the threads on the bed. Try extra hard to be accurate with driles, and go in gently to prevent chipping


If you don't have a 90 degree clamp to secure on the board, just make one! :)
Altenratively, you can mark two opposize corners on the board, and reset zero on those markings between passes. You need to be accurate in your markings. Measure thrice!

"""

import adsk.core, adsk.fusion, adsk.cam, traceback
import math

maxExceptions = 4 # script will not show more exceptions than this
exceptionUICounter = 0 
cleanModel = True       # script will remove objects and stetches from the project - simplifies script debug

# 1. General Rendering configuration
publishToCommunity = True       # fast setting to use before export to GrabCad or updating GitHub renders. Set to false when you play with parameters
showInfoMessages = True         # Shows UI pop-ups with information
renderBed = False               # Use for debug and visualisation
renderSpoilboard = True         # set to true for machinning, set to false to validate spoilboard design 
centerSpoilboard = False   # set to false if you want to move spoilboard around the board

# WARNING: be careful with next two settings
# Make sure to have some kind of padding or older spoilboard when running job while using these parameters
renderAdditionalStock = False   # renders spoilboard virtually thicker to render hole tips
ensureThroughHoles = True       # calulates hole depths to ensure that they will clear the stock sheet       

turnModel = True        # Turn model 90 degrees for easier alignment. See instruction above to see how it works
twoPassMilling = False   # mill only half of the model (split by X) for two-step marking process    
                        # this requires the holes to symmetrical
                        # Two pass milling is currently not supported if you want to shift the spoilboard from the center
                        # TODO: think how to implement to pass milling for any position of the board


markCornersAsMountingPoints = True     # This will automatically label the corner holes as mounting points

if publishToCommunity: # override some debug settings when publishing to community
    showInfoMessages = True
    renderBed = True
    renderSpoilboard = True
    renderAdditionalStock = False
    ensureThroughHoles = True
    turnModel = False
    twoPassMilling = False
    cleanModel = False
    centerSpoilboard = True   # set to false if you want to move spoilboard around the board
    markCornersAsMountingPoints = False

#  2. Physical dimensions: (super important)
# bed dimensions
bedXdimension = 360
bedYdimension = 300
bedMetricThread = 6 # mm

# it's ok to use smaller spoilboard sheet, the pattern will be centered
#spoilboardSheetXdimenstion = 355
#spoilboardSheetYdimenstion = 279

spoilboardSheetXdimenstion = 152 # + (360-152)
spoilboardSheetYdimenstion = 254 #+ (300-254)

spoilboardCornerX = 25 # used if not centerSpoilboard, will set to center if not defined
spoilboardCornerY = (bedYdimension-spoilboardSheetYdimenstion) # used if not centerSpoilboard, will set to center if not defined



stockThickness = 25.4 # how thick is the spoilboard material
bedThickness = 8

# Screw that mounts spoilboard to the bed:
# setup for countersunk M6:
screwCountersunkAngle = 90  # 90 is default for metric screws. set to 0 for straight pocket   
                                # for best one-tool operation, ensure your working bit has the same tip angle
screwCountersunkDepth = 3.5 # Set to 0 if don't want machined countersink or pocket at all
screwHeadWidth = 13.5         # screw head diameter. If you want - add some tolerance to create a bit deeper countersink


# setup for Socket Head:
screwCountersunkAngle = 0 # if we have flat head, we need to sink it deeper
screwHeadWidth = 13 # wide enough to use a washer and have some room for alignment
screwCountersunkDepth = stockThickness - 6 # sinking screw if thickness allows, leaving only 6 mm for support


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

if centerSpoilboard or not ('spoilboardCornerX' in vars() or 'spoilboardCornerX' in globals()):
    spoilboardCornerX = (bedXdimension - spoilboardSheetXdimenstion)/2     

if centerSpoilboard or not ('spoilboardCornerY' in vars() or 'spoilboardCornerY' in globals()):
    spoilboardCornerY = (bedYdimension - spoilboardSheetYdimenstion)/2

    
#Spoilboard corner on the bed - X: 2.5 Y: 10

zeroMarkDepth = .1 # how deep to mill mark for the other center point
zeroMarkWidth = 4

chamferWidth = 0 # chamfer for each hole. 
# Keep in mind, that if you are going to face the spoilboard after installing, some of the chamfer will be faced down.
# So if you want chamfer, keep it wider than the depth of your face operation
# Alternatively - set to 0 and configure in chamfer operaion

chamferHolesAngle = millBitPointAngle 

holeDiameter = bedMetricThread + 2 # allowing some wiggle room. ignored when optimised for milling
throughHoleToolClearance = 0.5 # how deep we want the tool to go under the holes to ensure clean bottom cut
# TODO: think, maybe this is not important for Autodesk fusion

cncBedClearance = 1 # protection parameter - how close do we want to get to the cnc bed to not ruin it

spoilboardEdgeKeepOut = 5 # How close can a hole get to the edge of spoilboard for integrity 
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
    # Iterate over the points array and add them to the sketch
    for point in points:
        x, y, mounting = point  # Extract x and y coordinates
        if mounting == mountingHoles:
            sketchPoint = adsk.core.Point3D.create(toCM(x + shiftX), toCM(y + shiftY), 0)  # Create a Fusion 360 point
            sketch.sketchPoints.add(sketchPoint)  # Add the point to the sketch
    
    sketch.sketchPoints.item(0).deleteMe()
    return sketch


def getSketchPointCoordinates(sketchPoint):
    pointGeometry = sketchPoint.geometry
    x = pointGeometry.x
    y = pointGeometry.y
    return f"({x}, {y})"

def createHolesFromSketch(targetBody, points, diameter, depth, countersinkDiameter=0, countersinkAngle=0, millTipAngle=0):
    # Iterate through all sketch points and create holes
    holes = rootComp.features.holeFeatures

    #skipFirst = True 
    #points.sketchPoints.item(0).deleteMe()
    collection = adsk.core.ObjectCollection.create()
    skipFirst = True # hack to avoud first point on the sketch - zero,zero
    hasPoints = False
    for sketchPoint in points.sketchPoints:
        if skipFirst:
            skipFirst = False
            continue
        collection.add(sketchPoint)
        hasPoints = True
        
    if not hasPoints:   # no actual points were added, return
        return
    
    try:
        if countersinkAngle and countersinkDiameter > diameter:
            holeInput = holes.createCountersinkInput(createMMValue(diameter), createMMValue(countersinkDiameter), createDegValue(countersinkAngle))
        elif countersinkDiameter > diameter: # TODO: support counterbore depth
            holeInput = holes.createCounterboreInput(createMMValue(diameter), createMMValue(countersinkDiameter), createMMValue(screwCountersunkDepth))
        else:
            holeInput = holes.createSimpleInput(createMMValue(diameter))

        holeInput.participantBodies = [targetBody]

        holeInput.setPositionBySketchPoints(collection)
        holeInput.setDistanceExtent(createMMValue(depth))

        if millTipAngle:
            holeInput.tipAngle = createDegValue(millTipAngle)        
        holes.add(holeInput)
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
    try:
        
        holeTipDepth = 0 if (millBitPointAngle==0 or millBitPointAngle==180) else (holeDiameter/math.tan(millBitPointAngle/2 * math.pi/180)/2)
        throughHoleStockClearance = (throughHoleToolClearance + holeTipDepth) if ensureThroughHoles else 0
        additionalStock = throughHoleStockClearance + (cncBedClearance if ensureThroughHoles else 0)

        spoilboardSheetThickness = stockThickness + (additionalStock if renderAdditionalStock else 0)
        holeMaxDepth = stockThickness + (additionalStock if ensureThroughHoles else 0) - cncBedClearance

        if ensureThroughHoles and ui and showInfoMessages:
            ui.messageBox("Ensure clearance between stock and cnc bed: {0:.3f} mm".format(additionalStock))
            #ui.messageBox("holeTipDepth:{0:.3f}\nthroughHoleToolClearance:{1:.3f}\ncncBedClearance:{2:.3f}\nthroughHoleStockClearance:{3:.3f}\nadditionalStock:{4:.3f}\nspoilboardSheetThickness:{5:.3f}\nholeMaxDepth:{6:.3f}".format(holeTipDepth,throughHoleToolClearance,cncBedClearance,throughHoleStockClearance,additionalStock,spoilboardSheetThickness,holeMaxDepth))


        supportOversizeSpoilboard = False # this checks that Spoilboard sheet is smaller than the board. 
                                        # change this value only if you understand what you are doing

        if not supportOversizeSpoilboard:
            assert bedXdimension >= spoilboardSheetXdimenstion, "spoilboard is too wide for X axis"
            assert bedYdimension >= spoilboardSheetYdimenstion, "spoilboard is too long for Y axis"
        if validateCountersunkDepth and screwCountersunkDepth>0:
            assert ensureThroughHoles or (screwCountersunkDepth <= holeMaxDepth), "max hole depth is not deep enough for countrsunk, min holeMaxDepth: " + str(screwCountersunkDepth)
            assert screwCountersunkAngle >= 0 and screwCountersunkAngle <= 180, "screwCountersunkAngle is out of range"        
            if screwCountersunkAngle > 0:
                requiredCounterSunkDepth = (screwHeadWidth - holeDiameter)/2/ math.tan(screwCountersunkAngle/2 * math.pi/180)/2
                assert requiredCounterSunkDepth <= screwCountersunkDepth, "countersunk is too shallow for this angle, min screwCountersunkDepth: " + str(requiredCounterSunkDepth)

        # Completing holes array with symmetrical values
        if boardXsymmetrical:
            holes += [[bedXdimension - elem[0], elem[1], elem[2]] for elem in holes]

        if boardYsymmetrical:
            holes += [[elem[0], bedYdimension - elem[1], elem[2]] for elem in holes]

        # remove dublicates that happen if some points are directly in the middle of the board
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
        holes = remove_duplicate_holes(holes)

        # realign all holes to the spoilboard system of coordinates
        spoilboardXShift = (bedXdimension - spoilboardSheetXdimenstion) / 2 if centerSpoilboard else spoilboardCornerX
        spoilboardYShift = (bedYdimension - spoilboardSheetYdimenstion) / 2 if centerSpoilboard else spoilboardCornerY
        baseHoles = [[elem[0] - spoilboardXShift, elem[1] - spoilboardYShift, elem[2]] for elem in holes]

        # remove points that are too close to the edges:
        realKeepout = spoilboardEdgeKeepOut + holeDiameter/2
        def spoilboardHoleCheck(hole):
            return hole[0] >= realKeepout and hole[1] >= realKeepout and hole[0] <= spoilboardSheetXdimenstion - realKeepout and hole[1] <= spoilboardSheetYdimenstion - realKeepout    
        
        spoilboardHoles = [[elem[0],elem[1],elem[2]] for elem in baseHoles if spoilboardHoleCheck(elem)] 


        # getting the coordinates that should be 0,0 - aligning on the first hole
        centerPoint = spoilboardHoles[0]

        if twoPassMilling: # just cut the board in half, at this point we don't need original dimensions anymore
            """
            ok, here is new logic:

            we need to go through all holes, and pull out find shallow marks

            for each hole: if X coordinate <= spoilboardSheetXdimenstion/2 - keep it to drill AND remember max X coordinate
            Then find 

            """
            centerPoint = [0, spoilboardSheetYdimenstion, False]
            for hole in spoilboardHoles:
                if hole[0] > spoilboardSheetXdimenstion/2: # wrong side of the board, not milling
                    continue 
                if hole[0] < centerPoint[0]:  # not the closest to the middle
                    continue 
                if hole[1] > centerPoint[1]:  # not the closest to the edge
                    continue 
                centerPoint = hole

            secondPassCenterPoint = [spoilboardSheetXdimenstion, 0, False]
            for hole in spoilboardHoles:
                if hole[0] <= spoilboardSheetXdimenstion/2: # wrong side - milling, but not centering here
                    continue
                if hole[0] > secondPassCenterPoint[0]:  # not the closest to the middle
                    continue 
                if hole[1] < secondPassCenterPoint[1]:  # not the closest to the edge
                    continue 
                secondPassCenterPoint = hole

            spoilboardHoles = [elem for elem in spoilboardHoles if elem[0]<=spoilboardSheetXdimenstion/2] # remove points that won't be rendered
            spoilboardSheetXdimenstion = secondPassCenterPoint[0] + realKeepout # cut the board
        #else:

        if markCornersAsMountingPoints:
            def findCorner(top, left, holes):
                cornerY = spoilboardSheetYdimenstion if top else 0
                cornerX = spoilboardSheetXdimenstion if left else 0
                magicX = 1 if left else -1
                magicY = 1 if top else -1
                corner = [cornerX,cornerY,False]

                for hole in holes:
                    if hole[1]*magicY > corner[1]*magicY: 
                        continue 
                    if hole[0]*magicX > corner[0]*magicX: 
                        continue 
                    corner = hole
                return corner
            
            # iterate through spoilboardHoles, find right-most and leftmost
            findCorner(True,True,spoilboardHoles)[2] = True
            findCorner(True,False,spoilboardHoles)[2] = True
            findCorner(False,True,spoilboardHoles)[2] = True
            findCorner(False,False,spoilboardHoles)[2] = True
            

        if ui and showInfoMessages:
            ui.messageBox("Mark the zero on spoilboard - X: {} Y: {}".format(centerPoint[0],centerPoint[1]));

        if turnModel:  # to turn model - swap X and Y everywhere
            (bedXdimension, bedYdimension) = (bedYdimension, bedXdimension)
            (spoilboardSheetXdimenstion, spoilboardSheetYdimenstion) = (spoilboardSheetYdimenstion, spoilboardSheetXdimenstion)
            (spoilboardXShift, spoilboardYShift) =  (spoilboardYShift, spoilboardXShift)
            if twoPassMilling:
                (secondPassCenterPoint[0],secondPassCenterPoint[1]) = (secondPassCenterPoint[1],secondPassCenterPoint[0])
            for hole in spoilboardHoles:
                (hole[0], hole[1]) = (hole[1], hole[0])

            for hole in baseHoles:
                (hole[0], hole[1]) = (hole[1], hole[0])
            
        if cleanModel:
            deleteAllBodiesAndSketches()

        xyPlane = rootComp.xYConstructionPlane
        mountingHoleCollection = createSketchWithPoints("Mounting points", rootComp, spoilboardHoles, xyPlane, True,  -centerPoint[0], -centerPoint[1])
        holeCollection = createSketchWithPoints("Drilling points", rootComp, spoilboardHoles, xyPlane, False, -centerPoint[0], -centerPoint[1])

        baseHoleCollection = createSketchWithPoints("Flatbed points", rootComp, baseHoles, xyPlane, False, -centerPoint[0], -centerPoint[1]) 
        baseHoleCollectionCorners = createSketchWithPoints("Flatbed points", rootComp, baseHoles, xyPlane, True, -centerPoint[0], -centerPoint[1]) 
            
        if renderBed:
            bed = renderBox("CNC bed", bedXdimension, bedYdimension, bedThickness, -centerPoint[0]-spoilboardXShift, -centerPoint[1]-spoilboardYShift, -bedThickness-spoilboardSheetThickness);
            createHolesFromSketch(bed, baseHoleCollection, bedMetricThread, 2*(bedThickness+spoilboardSheetThickness), 0, 0, 0)
            createHolesFromSketch(bed, baseHoleCollectionCorners, bedMetricThread, 2*(bedThickness+spoilboardSheetThickness), 0, 0, 0)

        if renderSpoilboard:
            spoilboard = renderBox("Spoilboard", spoilboardSheetXdimenstion, spoilboardSheetYdimenstion, spoilboardSheetThickness, -centerPoint[0], -centerPoint[1], -spoilboardSheetThickness);
            createHolesFromSketch(spoilboard, mountingHoleCollection, holeDiameter, holeMaxDepth-holeTipDepth, screwHeadWidth, screwCountersunkAngle, millBitPointAngle)
            createHolesFromSketch(spoilboard, holeCollection, holeDiameter, holeMaxDepth-holeTipDepth, holeDiameter + 2*chamferWidth, chamferHolesAngle, millBitPointAngle)
        
        if renderSpoilboard and twoPassMilling:
            marksCollection = createSketchWithPoints("Second pass zero point {},{},{}".format(secondPassCenterPoint[0],secondPassCenterPoint[1],secondPassCenterPoint[2]), rootComp, [secondPassCenterPoint,centerPoint], xyPlane, secondPassCenterPoint[2], -centerPoint[0], -centerPoint[1])
            createHolesFromSketch(spoilboard, marksCollection, zeroMarkWidth, zeroMarkDepth, 0, 0, millBitPointAngle)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
