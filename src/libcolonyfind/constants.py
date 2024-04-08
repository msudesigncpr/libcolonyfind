MIN_COLONY_DISTANCE = 0.01 
MIN_COLONY_RADIUS = 0.004 #FIXME THIS MAY BE TOO SMALL. I DO NOT KNOW. I NEED TO FIGURE IT OUT!

PETRI_DISH_ROI = 1.15            #### FIXME: CHANGE TO LIKE 0.4 OR SOMETHING

IMG_HEIGHT = 2448
IMG_WIDTH = 3264


# IMAGES_FOR_CFU_WIN_PATH = 'C:\\Users\\colon\\Downloads\\GUI\\src\\petri_dish_photos_raw'     # FIXME: uncomment when xy coordinates are unfucked 
# IMAGES_FOR_CFU_WSL_PATH = '/mnt/c/Users/colon/Downloads/GUI/src/petri_dish_photos_raw/'  # FIXME: uncomment when xy coordinates are unfucked 

# DO NOT CHANGE YOU'LL BREAK SHIT
CFU_WIN_PATH = '\\\\wsl.localhost/Debian/home/colon/OpenCFU'
CFU_CSV_DUMP_PREFIX_WSL = '../cfu_coords/'
# CFU_CSV_DUMP_PATH_WIN = '\\\\wsl.localhost/Debian/home/colon/cfu_coords' # TODO Can I call functions on files in wsl? what does the path look like?

# CFU_CSV_WIN_DUMP_PATH = 'C:\\Users\\colon\\Downloads\\GUI\\temp\\cfu_coords'
CFU_CSV_WIN_DUMP_PATH = 'C:\\Users\\John Fike\\OneDrive\\Documents\\Visual Studio 2022\\cap\\libcolonyfind\\cfu-csv' # FIXME REMOVE

IMAGES_FOR_CFU_WIN_PATH = 'C:\\Users\\colon\\Downloads\\GUI\\src\\4-5-images'  #### FIXME: Remove once coordinates unfucked
IMAGES_FOR_CFU_WSL_PATH = '/mnt/c/Users/colon/Downloads/GUI/src/4-5-images/' #### FIXME: Remove once coordinates unfucked

CAM_X_OFFSETS = [69.3,  68.5, 182, 182, 297.5, 412]
CAM_Y_OFFSETS = [52.5, -67,  52.5, -67, -67.5, -67]

WELLS =['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12',
        'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12',
        'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12',
        'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12',
        'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12',
        'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',                    
        'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12',
        'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11', 'H12']

# # ANNOTATION_IMAGE_INPUT_PATH = 'C:\\Users\\colon\\Downloads\\GUI\\src\\petri_dish_photos_raw' # FIXME: uncomment when xy coordinates are unfucked 
# ANNOTATION_IMAGE_INPUT_PATH = 'C:\\Users\\colon\\Downloads\\GUI\\src\\4-5-images'
# ANNOTATION_IMAGE_OUTPUT_PATH = 'C:\\Users\\colon\\Downloads\\GUI\\src\\annotated-images'

ANNOTATION_IMAGE_INPUT_PATH = 'C:\\Users\\John Fike\\OneDrive\\Documents\\Visual Studio 2022\\cap\\libcolonyfind\\4-5-images'
ANNOTATION_IMAGE_OUTPUT_PATH = 'C:\\Users\\John Fike\\OneDrive\\Documents\\Visual Studio 2022\\cap\\libcolonyfind\\annotated-images'

# CFU_CSV_DUMP_PATH_WSL = '/mnt/c/Users/colon/Downloads/GUI/src/cfu_csv/unmod/'


CAM_X = 162.307  #mm measured accross the x dir of camera
CAM_Y = 121.73 #mm measured accross the y dir of camera
