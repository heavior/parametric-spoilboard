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

import adsk.core, adsk.fusion, adsk.cam, traceback
import math

# 1. General Rendering configuration
publishToCommunity = False # fast setting to use before export to GrabCad or updating GitHub renders

renderBed = False       # Use for debug and visualisation
renderSpoilboard = True # set to true for machinning, set to false to validate spoilboard design
renderAdditionalStock = renderSpoilboard    # render additional stock under spoilboard. Change if need debugging

optimizeForMilling = True   # creates countours for milling with V-groove bits
ensureThroughHoles = not publishToCommunity and True  # WARNING: can mill into CNC bed if not careful
                            # This will make the model thicker than your stock to ensure that milling goes through thoroughly
                            # Make sure to have some kind of padding or older spoilboard when running task with this parameter

turnModel =      not publishToCommunity and True    # Turn model 90 degrees for easier alignment. See instruction to see how it works
twoPassMilling = not publishToCommunity and True    # render only half of the model (split by X) for two-step marking process    

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
        [80, 20],
        [140, 20],

    #row 2
        [50, 45],
        [110, 45],

    #row 3
        [20, 70],
        [80, 70],
        [140, 70],

    #row 4
        [110, 97.5],

    #row 5
        [70, 108],

    #row 6
        [20, 125],
        [140, 125],

    #row 7
        [70, bedYdimension/2],
        [110, bedYdimension/2],
]

# 4. Positioning and clearances (likely don't need to change)

centerSpoilboard = True   # set to false if you want to move spoilboard around the board
# if centerSpoilboard=false, change next two variables as needed:
spoilboardCornerX = (bedXdimension - spoilboardSheetXdimenstion)/2     
spoilboardCornerY = (bedYdimension - spoilboardSheetYdimenstion)/2
#Spoilboard corner on the bed - X: 2.5 Y: 10

limitMillingDepth = 2 # How deep to mill holes. Ignored when ensureThroughHoles is used

chamferHolesDepth = .5 # chamfer each hole to this depth. set to 0 to skip
chamferHolesAngle = millBitPointAngle # use the 

holeDiameter = bedMetricThread + 1 # allowing some wiggle room. ignored when optimised for milling
throughHoleToolClearance = .5 # how deep we want the tool to go under the holes to ensure clean bottom cut
cncBedClearance = 1 # protection parameter - how close do we want to get to the cnc bed to not ruin it

spoilboardEdgeKeepOut = 6 # How close can a hole get to the edge of spoilboard for integrity 
                           # (counterink can overflow into that zone)


# parameter validation and some prep calculations:
# check parameters
assert millBitPointAngle >= 0 and millBitPointAngle <= 180, "millBitPointAngle is out of range"
assert not optimizeForMilling or (millBitPointAngle==screwCountersunkAngle), "When optimising for milling, millBitPointAngle must be equal to screwCountersunkAngle"

millingTipDepth = 0 if (millBitPointAngle==0 or millBitPointAngle==180) else millBitThickness/math.tan(millBitPointAngle/2 * math.pi/2)/2
throughHoleStockClearance = (throughHoleToolClearance + millingTipDepth) if ensureThroughHoles else 0
additionalStock = throughHoleStockClearance + (cncBedClearance if ensureThroughHoles else 0)
                                               
if additionalStock > 0:
    print ("Ensure clearance between stock and cnc bed: " + str(additionalStock) + " mm")

spoilboardSheetThickness = stockThickness + additionalStock
millingDepth = spoilboardSheetThickness if ensureThroughHoles else limitMillingDepth
holeMaxDepth = (spoilboardSheetThickness if ensureThroughHoles else stockThickness) - cncBedClearance 

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


# Completing holes2 array with symmetrical values
if boardXsymmetrical:
    holes += [[bedXdimension - elem[0], elem[1], elem[2]] for elem in holes]
if boardYsymmetrical:
    holes += [[elem[0], bedYdimension - elem[1], elem[2]] for elem in holes]

spoilboardXShift = (bedXdimension - spoilboardSheetXdimenstion) / 2 if centerSpoilboard else spoilboardCornerX
spoilboardYShift = (bedYdimension - spoilboardSheetYdimenstion) / 2 if centerSpoilboard else spoilboardCornerY
spoilboardHoles = [[elem[0] - spoilboardXShift, elem[1] - spoilboardYShift, elem[2]] for elem in holes]

realKeepout = spoilboardEdgeKeepOut + holeDiameter/2

def spoilboardHoleCheck(hole):
    return hole[0] >= realKeepout and hole[1] >= realKeepout and hole[0] <= spoilboardSheetXdimenstion - realKeepout and hole[1] <= spoilboardSheetYdimenstion - realKeepout    
    
spoilboardHoles = [elem for elem in spoilboardHoles if spoilboardHoleCheck(elem)]

# now we have an array that's ready to use




def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        ui.messageBox('Hello script')
    
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
