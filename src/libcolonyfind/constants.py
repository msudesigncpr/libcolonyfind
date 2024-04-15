CFU_PATH = "/home/runner/work/libcolonyfind/libcolonyfind/OpenCFU"  # TODO make runner wd
"""
Path to wherever CFU is installed in WSL. Yes those four backslashes are necesary. No I don't like it either. 
"""

GSD_X = 174.45
"""
mm per pixel in the x direction
"""

GSD_Y = 125.84
"""
mm per pixel in the y direction
"""

"""
effectivley just conversion factors for going from mmm to pixels
"""

IMG_HEIGHT = 2448
IMG_WIDTH = 3264
"""
Image sizes are for the camera in the BOM: https://github.com/msudesigncpr/datasheets/blob/tonic/BOM.md
"""

MIN_COLONY_DISTANCE = 0.5
"""
Used by remove_unsampleable_colonies()
Defines the minimum distance allowed between the edges of two colonies
Neither colony will be sampled from if they are closer than this distance
This distance is in fractions of an image. Hopefully I remember to change that...
"""

MIN_COLONY_RADIUS = 1  # TODO: FIXME
"""
Used by remove_unsampleable_colonies()
Defines the minimum radius for a colony to be sampleable. 
Kind of just a potshot number right now. 
This distance is in fractions of an image. Hopefully I remember to change that...
"""

XLIMIT_MIN = -27.44
"""
Used by remove_unsampleable_colonies()
Defines the closest a colony can be to the x-axis origin in the two plates
closest to the x-axis origin.
"""

PETRI_DISH_ROI = 50  # TODO: FIXME
"""
Used by remove_unsampleable_colonies()
Defines distance from center of image colonies can be to be considered sampleable
This distance is in fractions of an image. Hopefully I remember to change that...
"""

WELLS = [
    "A1",
    "A2",
    "A3",
    "A4",
    "A5",
    "A6",
    "A7",
    "A8",
    "A9",
    "A10",
    "A11",
    "A12",
    "B1",
    "B2",
    "B3",
    "B4",
    "B5",
    "B6",
    "B7",
    "B8",
    "B9",
    "B10",
    "B11",
    "B12",
    "C1",
    "C2",
    "C3",
    "C4",
    "C5",
    "C6",
    "C7",
    "C8",
    "C9",
    "C10",
    "C11",
    "C12",
    "D1",
    "D2",
    "D3",
    "D4",
    "D5",
    "D6",
    "D7",
    "D8",
    "D9",
    "D10",
    "D11",
    "D12",
    "E1",
    "E2",
    "E3",
    "E4",
    "E5",
    "E6",
    "E7",
    "E8",
    "E9",
    "E10",
    "E11",
    "E12",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
    "G1",
    "G2",
    "G3",
    "G4",
    "G5",
    "G6",
    "G7",
    "G8",
    "G9",
    "G10",
    "G11",
    "G12",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "H7",
    "H8",
    "H9",
    "H10",
    "H11",
    "H12",
]
"""
Used by annotate_images() to write the well each colony is destined for on the image
"""
