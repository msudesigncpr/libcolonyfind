MIN_COLONY_DISTANCE = 0.01 
MIN_COLONY_RADIUS = 0.002 #TODO THIS MAY BE TOO SMALL. I DO NOT KNOW. I NEED TO FIGURE IT OUT!


CFU_RAW_IMAGE_PATH = 'C:\\Users\\colon\\Downloads\\GUI\\src\\4-5-images'  #### TODO: Change to be raw images or wherever this infernal fucking machine puts images it takes
CFU_RAW_IMAGE_PATH_WSL = '/mnt/c/Users/colon/Downloads/GUI/src/4-5-images/' #### TODO: Change to be raw images or wherever this infernal fucking machine puts images it takes

# CFU_RAW_IMAGE_PATH = 'C:\\Users\\colon\\Downloads\\GUI\\src\\petri_dish_photos_raw'     # HACK: uncomment when xy coordinates are unfucked 
# CFU_RAW_IMAGE_PATH_WSL = '/mnt/c/Users/colon/Downloads/GUI/src/petri_dish_photos_raw/'  # HACK: uncomment when xy coordinates are unfucked 

# ANNOTATION_IMAGE_INPUT_PATH = 'C:\\Users\\colon\\Downloads\\GUI\\src\\petri_dish_photos_raw' # HACK: uncomment when xy coordinates are unfucked 
ANNOTATION_IMAGE_INPUT_PATH = 'C:\\Users\\colon\\Downloads\\GUI\\src\\4-5-images'
ANNOTATION_IMAGE_OUTPUT_PATH = 'C:\\Users\\colon\\Downloads\\GUI\\src\\annotated-images'


# CFU_CSV_DUMP_PATH_WSL = '/mnt/c/Users/colon/Downloads/GUI/src/cfu_csv/unmod/'

# DO NOT CHANGE YOU'LL BREAK SHIT
CFU_PATH_WIN = '\\\\wsl.localhost/Debian/home/colon/OpenCFU'
CFU_CSV_DUMP_PREFIX_WSL = '../cfu_coords/'
# CFU_CSV_DUMP_PATH_WIN = '\\\\wsl.localhost/Debian/home/colon/cfu_coords'


PETRI_DISH_ROI = 0.15                                                       #### HACK: CHANGE TO LIKE 0.4 OR SOMETHING

IMG_HEIGHT = 2448
IMG_WIDTH = 3264


CAM_X = 162.307  #mm measured accross the x dir of camera
CAM_Y = 121.73 #mm measured accross the y dir of camera

CAM_POS_X1 = 69.3
CAM_POS_Y1 = 52.5
#CHANGED X+4 AND Y-10
CAM_POS_X2 = 68.5
CAM_POS_Y2 = -67
#CHANGED X+4 AND Y-8
CAM_POS_X3 = 182
CAM_POS_Y3 = 52.5
#CHANGED X+4 AND Y-8
CAM_POS_X4 = 182
CAM_POS_Y4 = -67
#CHANGED X+4 AND Y-8
CAM_POS_X5 = 297.5
CAM_POS_Y5 = -67.5
#CHANGED X+4 AND Y-8
CAM_POSX6 = 412
CAMPOS_Y6 = -67