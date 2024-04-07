from pathlib import WindowsPath
import subprocess
import logging
import constants_test as CONSTANTS
import cv2
import csv
import os


# lines with HACK are the ones you should probably change after xy coords are unfucked

# FIXME on ln 200. wrong coordinate calculation is taking place

# TODO: Play with CFU options to make it better maybe------------------------------------------0%
# TODO: (!) Fix path issues--------------------------------------------------------------------0%
# TODO: Fix logging----------------------------------------------------------------------------80%
# TODO: Fix error handling---------------------------------------------------------------------40%
# TODO: Fix metadata creation------------------------------------------------------------------90ish%
# TODO: (!!!) Do something other than create thousands of temporary .txt files.
#       |----> CFU currently generates csvs, which are dumped into the project directory
#              I tried to pipe them directly into stuff  without wsl mv but it didn't work, so
#               TODO: fix opencfu csv handling 




LOGLEVEL = logging.INFO
logging.basicConfig(
    format="%(asctime)s: %(message)s",
    level=LOGLEVEL,
    datefmt="%H:%M:%S",
)



def find_colonies():
    # run_cfu()
    coords = parse_cfu_csv()
    drive_coords = remove_doublets(coords)
    return drive_coords

def run_cfu(img_folder_path = CONSTANTS.CFU_RAW_IMAGE_PATH, cfu_raw_images = CONSTANTS.CFU_RAW_IMAGE_PATH_WSL, csv_dump_path_win = CONSTANTS.CFU_CSV_DUMP_PATH_WIN):
    """
    runs WSL to execute OpenCFU on images in img_folder_path
    cfu_raw_images is the wsl path to the images. this is in a different format
    my current fix is to just have two paths, one for windows (img_folder_path)
    and one for linux (cfu_raw_images)

    cfu generates csvs with locations to the colonies it has found, and puts it in
    cfu_csv_dump_path (another linux path)

    for example,
    img_folder_path 'C:\\Users\\colon\\...' -- CFU reads images from here. 
    cfu_raw_images '/mnt/c/Users/colon/...' -- CFU reads images from here. SAME AS IMG_FOLDER_PATH BUT IN LINUX FORMAT
    cfu_csv_dump_path '/mnt/c/Users/colon/...' -- CFU CSVs are dumped here
    """
    logging.info("Initializing OpenCFU...")
    os.chdir(WindowsPath(CONSTANTS.CFU_PATH_WIN))

    try: 
        # FIXME: access denied to dump directory, cannot create
        # logging.info("Creating CFU CSV dump directory...")
        # try: 
        #     if not os.path.exists(cfu_csv_dump_path): os.makedirs(cfu_csv_dump_path)
        # except Exception as e:
        #     logging.error("Error creating CFU CSV dump directory: %s.", e)
        #     raise("Error creating CFU CSV dump directory")

        for image in os.listdir(img_folder_path):
            base_file_name = os.path.splitext(os.path.basename(image))[0]
            logging.info("Processing image %s", base_file_name)

            cfu_image_path = cfu_raw_images + base_file_name + ".jpg"
            cfu_coord_path = CONSTANTS.CFU_CSV_DUMP_PREFIX_WSL + base_file_name + '.csv' # path to coords for individual colony

            # run cfu on images and move resultant coords to csv dumppath
            subprocess.run(['wsl', './opencfu', '-i', cfu_image_path, '>', cfu_coord_path])
            subprocess.run(['wsl', 'mv', cfu_coord_path, csv_dump_path_win])



        logging.info("CFU processing complete")

    except Exception as e:
        logging.error("CFU processing failed: %s", e)
        raise("Error running CFU")


def parse_cfu_csv(csv_path = CONSTANTS.CFU_CSV_DUMP_PATH_WIN, ):
    """
    openCFU generates .csv files, which are moved to project directory (for now, see TODO above)
    This function reads the .csv files, extracts the colony coordinates, and writes them to a .txt file
    these coordinates are fractional (YOLO format)
    """
    logging.info("Parsing CFU CSVs...")

    coords = {}

    offset_index = 0
    try:
        for csv_file in os.listdir(csv_path):
            temp = []
            base_file_name = os.path.splitext(os.path.basename(csv_file))[0]
            logging.info("Processing CFU CSV %s", base_file_name)

            with open(os.path.join(csv_path, csv_file), 'r', newline='') as infile:
                reader = csv.reader(infile)

                rows = list(reader)
                data = rows[1:]

                # loop thru every row in the csv file, extract the x, y, and r values, and throw them in the coords dict
                for row in data:
                    x = float(row[1])
                    y = float(row[2])
                    r = float(row[7])
                    temp.append [x, y, r]
                    
                coords[base_file_name] = temp
                offset_index = offset_index + 1

        logging.info("CFU CSV procecssing complete")
        return coords

        #FIXME 
        # logging.info("Destroying CFU CSV dump directory[%s]...", coords_to_convert)
        # try:
        #     os.rmdir(coords_to_convert)
        #     if os.path.exists(coords_to_convert): shutil.rmtree("valid_colony_list")
        # except Exception as e:
        #     logging.error("Error destroying CFU CSV dump directory: %s.", e)
        #     raise("Error destroying CFU CSV dump directory")
        

    except Exception as e:
        logging.error("CFU CSV processing failed: %s", e)   #TODO fix logging
        raise("Error parsing CFU CSVs")

def remove_doublets(coords, petri_dish_roi = CONSTANTS.PETRI_DISH_ROI, min_colony_dist = CONSTANTS.MIN_COLONY_DISTANCE, min_colony_radius = CONSTANTS.MIN_COLONY_RADIUS, img_height = CONSTANTS.IMG_HEIGHT, img_width = CONSTANTS.IMG_WIDTH, cam_x = CONSTANTS.CAM_X, cam_y = CONSTANTS.CAM_Y, cam_x_offsets = CONSTANTS.CAM_X_OFFSETS, cam_y_offsets = CONSTANTS.CAM_Y_OFFSETS, wells = CONSTANTS.WELLS):
    logging.info("Removing doublet colonies...")
    good_colony_counter = 0


    # the dictionary has the file name as the key, and the value is a set of coordinates to each colony in the iamge
    # 
    # each sublist is a coordinate set for a colony
    # ex
    # coords = {
    #           'file_name" : coor_set
    #           'file1': [[x1, y1, r1], [x2, y2, r2], [x3, y3, r3]],
    #           'file2': [[x1, y1, r1], [x2, y2, r2], [x3, y3, r3]],
    #           'file3': [[x1, y1, r1], [x2, y2, r2], [x3, y3, r3]]
    #          }
    offset_index_counter = 0
    drive_coords = []
    annotation_coords = {}
    well_plate_index_counter = 0

    for file_name, coord_set in coords.items():
        logging.info("----------Processing coord file %s----------", file_name)
        bad_colony_counter = 0
        doublet_colony_counter = 0
        too_small_colony_counter = 0
        over_edge_colony_counter = 0
        offset_index_counter = offset_index_counter + 1
        

        for main_colony_line in coord_set:

            bad_colony = False

            main_colony_x = float(main_colony_line[1])
            main_colony_y = float(main_colony_line[2])
            main_colony_r = float(main_colony_line[3])

            """ 
            check if the colony is in the petri dish
            if it is, check if it is big enough
            if it is, check if there are any nearby colonies that would make it un-sampleable
            """
            if distance_from_center(main_colony_x, main_colony_y) > petri_dish_roi: 
                bad_colony = True
                over_edge_colony_counter = True 
            elif main_colony_r < min_colony_radius:
                bad_colony = True
                too_small_colony_counter = too_small_colony_counter + 1
            else:
                for neighbor_colony_line in coord_set: # mmm O(n^2). great.
                    neighbor_colony_x = float(neighbor_colony_line[1])
                    neighbor_colony_y = float(neighbor_colony_line[2])
                    neighbor_colony_r = float(neighbor_colony_line[3])
                    
                    
                    # bool for if the current neighbor is the main colony   
                    neighbor_is_main = neighbor_colony_line == main_colony_line 
                    # bool for if the main colony is a doublet (is too close to neighbor)
                    main_is_doublet = distance_between_colonies(main_colony_x, main_colony_y, main_colony_r, neighbor_colony_x, neighbor_colony_y, neighbor_colony_r) < min_colony_dist 

                    if (not neighbor_is_main) and main_is_doublet:
                        bad_colony = True
                        doublet_colony_counter = doublet_colony_counter + 1
                    

            if (not bad_colony) and (not drive_coords.__contains__(main_colony_line)):
                baseplate_x = (cam_y_offsets[offset_index_counter] - (cam_x / 2)) + (main_colony_x/img_width) * cam_x # FIXME THIS IS PROBABLY WRONG
                baseplate_y = (cam_x_offsets[offset_index_counter] - (cam_y / 2)) + (main_colony_y/img_height) * cam_y
                drive_coords.extend([baseplate_x, baseplate_y])

                well = wells[well_plate_index_counter]
                annotation_coords[file_name].append([main_colony_x, main_colony_y, main_colony_r, well])
                well_plate_index_counter = well_plate_index_counter + 1
            
                good_colony_counter = good_colony_counter + 1
            elif bad_colony:
                bad_colony_counter = bad_colony_counter + 1


        logging.info("TOO SMALL:..........%s | DOUBLET:.........%s  | OUTSIDE DISH:............%s " , too_small_colony_counter, doublet_colony_counter, over_edge_colony_counter)
        # logging.info("DETECTED:...........%s | BAD:............ %s | GOOD:....................%s", len(lines), bad_colony_counter,  len(good_colonies))
        logging.info(" ")
    logging.info("Doublet removal complete. %s colonies can be sampled from!", good_colony_counter)
    logging.info(" ")
    return drive_coords, annotation_coords

def distance_from_center(x0, y0):
    x_dist = abs(x0 - 0.5) ** 2
    y_dist = abs(y0 - 0.5) ** 2
    distance = (x_dist + y_dist) ** 0.5
    return distance

def distance_between_colonies(x0, y0, r0, x1, y1, r1):
    x_dist = abs(x0 - x1) ** 2
    y_dist = abs(y0 - y1) ** 2
    distance = (x_dist + y_dist) ** 0.5
    # check if they are overlapping. return -1 if they are
    if distance > (r0 + r1):            
        return distance - (r0 + r1)
    else: return -1


# FIXME 
def annotate_images(coords, annotation_image_input_path = CONSTANTS.ANNOTATION_IMAGE_INPUT_PATH, annotation_output_path = CONSTANTS.ANNOTATION_IMAGE_OUTPUT_PATH, annotation_coord_path = CONSTANTS.ANNOTATION_COORD_PATH, petri_dish_roi = CONSTANTS.PETRI_DISH_ROI, image_height = CONSTANTS.IMG_HEIGHT, image_width = CONSTANTS.IMG_WIDTH):
    try:
        logging.info("Creating annotated images...")
        if not os.path.exists(annotation_output_path):
            logging.info("Creating annotated image directory: %s", annotation_output_path)
            os.makedirs(annotation_output_path)
        

        # Loop through each image file in the specified folder path
        for file_name, coord_set in coords.items():
            
            image = cv2.imread(os.path.join(annotation_image_input_path, str(file_name) + '.jpg'))
        

            # Open the colony coordinates text file corresponding to the current image

            if len(coord_set) > 0:
                # Iterate over each line in the text file
                for colony_line in coord_set:
                    try:
                        x = int(float(colony_line[1]))
                        y = int(float(colony_line[2]))
                        r = int(float(colony_line[3]))

                        if len(colony_line)>3: 
                            colony_number = str(colony_line[4])
                            font_size = 2
                        else: 
                            colony_number = colony_line[3][:6]
                            font_size = 1

                    except Exception as e:
                        logging.error("Error extracting colony number: %s", e)
                        raise("Improperly formatted colony coordinates file")

                    # draw circles around colonies, and write colony number next to them
                    try:
                        cv2.circle(image, (x, y), int(r*2), (0, 0, 0), 2)
                        cv2.putText( image, str(colony_number), (int(x + 30), int(y - 30)), cv2.FONT_HERSHEY_SIMPLEX, font_size, (0, 0, 0), 1) 
                    except Exception as e:
                        logging.error("Error drawing stuff on and near colonies")
                        raise("Error drawing stuff on and near colonies")

            cv2.circle(image, (int(0.5*image_width),int(0.5*image_height)), int(petri_dish_roi * image_width), (0,255,0), 2)    # HACK:remove when xy coordinates are unfucked. shows where edges of petri dish should be

            save_path = os.path.join(annotation_output_path, str(file_name + '.jpg'))
            logging.info("Saving image with %s colonies marked to %s", len(coord_set), save_path)
            # logging.info("Marked image saved" + str(base_file_name) + ".jpg") # TODO: fix logging
            try:
                cv2.imwrite(save_path, image)
            except Exception as e:
                logging.error("Error saving annotated images to: %s", save_path)
                raise("Error saving annotated images")

        logging.info("Annotated image creation complete")
    
    except Exception as e:
        logging.info("An error occured while annotating images: ", e)
        raise("Error creating metadata")


