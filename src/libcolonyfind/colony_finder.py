import constants_test as CONSTANTS
from pathlib import WindowsPath
import subprocess
import logging
import random
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

# TODO Create drive coords
                # x = (cam_y_offsets[dish_offset_index_counter] - (cam_x / 2)) + (main_colony_x/img_width) * cam_x # FIXME THIS IS PROBABLY WRONG
                # y = (cam_x_offsets[dish_offset_index_counter] - (cam_y / 2)) + (main_colony_y/img_height) * cam_y


LOGLEVEL = logging.INFO
logging.basicConfig(
    format="%(asctime)s: %(message)s",
    level=LOGLEVEL,
    datefmt="%H:%M:%S",
)

class colony_finder:

    def __init__(self):
        self.raw_coords = {}
        self.sampleable_coords = {}
        self.annotated_images = {}
        self.drive_coords = []

    def find_colonies(self):
        # run_cfu()
        self.raw_coords = self.parse_cfu_csv()
        self.sampleable_coords = self.remove_unsampleable_colonies(self.raw_coords)
        self.sampleable_coords = self.remove_extra_colonies(self.sampleable_coords)
        self.annotated_images = self.annotate_images(self.sampleable_coords)
        self.drive_coords = self.generate_drive_coords(self.sampleable_coords)


def find_colonies():
    # run_cfu()
    coords = parse_cfu_csv()
    coords = remove_unsampleable_colonies(coords)
    coords = remove_extra_colonies(coords)
    annotate_images(coords)
    drive_coords = generate_drive_coords(coords)
    return drive_coords

def run_cfu(images_for_cfu_win_path = CONSTANTS.IMAGES_FOR_CFU_WIN_PATH, images_for_cfu_wsl_path = CONSTANTS.IMAGES_FOR_CFU_WSL_PATH, cfu_csv_win_dump_path = CONSTANTS.CFU_CSV_WIN_DUMP_PATH, cfu_csv_dump_prefix_wsl = CONSTANTS.CFU_CSV_DUMP_PREFIX_WSL, cfu_win_path = CONSTANTS.CFU_WIN_PATH):
    """uses WSL to run OpenCFU on images in img_folder_path
    OpenCFU generates .csv files, which are moved to project directory (for now, see TODO above)"""
    
    # logging.info(" ")

    try:
        logging.info("Initializing OpenCFU...")
        os.chdir(WindowsPath(cfu_win_path))
    except:
        logging.critical("Error initializing OpenCFU")
        raise RuntimeError("Error initializing OpenCFU")

    try: 
        # FIXME: access denied to dump directory, cannot create
        # logging.info("Creating CFU CSV dump directory...")
        # try: 
        #     if not os.path.exists(cfu_csv_dump_path): os.makedirs(cfu_csv_dump_path)
        # except Exception as e:
        #     logging.error("Error creating CFU CSV dump directory: %s.", e)
        #     raise("Error creating CFU CSV dump directory")

        for image in os.listdir(images_for_cfu_win_path):
            base_file_name = os.path.splitext(os.path.basename(image))[0]
            logging.info("Processing image %s", base_file_name)

            cfu_image_wsl_path = images_for_cfu_wsl_path + base_file_name + ".jpg" # where cfu will look for img
            cfu_coord_wsl_path = cfu_csv_dump_prefix_wsl + base_file_name + '.csv' # where cfu will place coords to colonies it finds (ex /mnt/c/Users/colon/Downloads/GUI/src/cfu_coords/dish_0.csv)

            try:
                # run cfu on images and move resultant coords to csv dumppath
                subprocess.run(['wsl', './opencfu', '-i', cfu_image_wsl_path, '>', cfu_coord_wsl_path]) # TODO can I pipe to project dir path?
                subprocess.run(['wsl', 'mv', cfu_coord_wsl_path, cfu_csv_win_dump_path])
            except:
                logging.critical("WSL fucking exploded")
                raise RuntimeError("WSL fucking exploded")

        logging.info("CFU processing complete")
        # logging.info(" ")

    except:
        logging.critical("CFU processing failed, terminating...")
        raise RuntimeError("CFU processing failed, terminating...")

def parse_cfu_csv(csv_win_path = CONSTANTS.CFU_CSV_WIN_DUMP_PATH):
    """
    openCFU generates .csv files, which are moved to project directory (for now, see TODO above)
    This function reads the .csv files, extracts the colony coordinates returns a dict with the file name as the key, and the value as a list of coordinates for each colony in the image
    for ex:
    coords = {
                'file1': [[x1, y1, r1], [x2, y2, r2], [x3, y3, r3]],
                'file2': [[x1, y1, r1], [x2, y2, r2], [x3, y3, r3]],
                'file3': [[x1, y1, r1], [x2, y2, r2], [x3, y3, r3]]
    }
    """
    # logging.info(" ")
    logging.info("Parsing CFU CSVs...")

    coords = {}
    offset_index = 0

    try:
        for csv_file in os.listdir(csv_win_path):
            temp = []
            base_file_name = os.path.splitext(os.path.basename(csv_file))[0]
            logging.info("Processing CFU CSV %s", base_file_name)

            # read in csvs 
            with open(os.path.join(csv_win_path, csv_file), 'r', newline='') as infile:
                reader = csv.reader(infile)

                rows = list(reader)
                data = rows[1:]

                # loop thru every row in the csv file, extract the x, y, and r values, and throw them in the coords dict
                for row in data:
                    x = float(row[1])
                    y = float(row[2])
                    r = float(row[7])
                    temp.append([x, y, r])
                    
            coords[base_file_name] = temp
            offset_index = offset_index + 1

        logging.info("CFU CSV procecssing complete")
        # logging.info(" ")
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
        logging.critical("CFU CSV processing failed: %s", e)   #TODO fix logging
        raise RuntimeError("CFU CSV processing failed: %s", e)

def remove_unsampleable_colonies(coords, petri_dish_roi = CONSTANTS.PETRI_DISH_ROI, min_colony_dist = CONSTANTS.MIN_COLONY_DISTANCE, min_colony_radius = CONSTANTS.MIN_COLONY_RADIUS, img_height = CONSTANTS.IMG_HEIGHT, img_width = CONSTANTS.IMG_WIDTH):
    '''
    Take in a dict with coords, and: remove colonies that are too close to the edge of the petri dish, too small, or too close to other colonies
    temp_coords is a dict with the same keys as coords, but the values are lists of coordinates for colonies that are sampleable
    '''
    # logging.info(" ")
    logging.info("Removing unsampleable colonies...")

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
    temp_coords = {}
    good_colony_counter = 0

    for file_name, coord_list in coords.items():
        logging.info("----------Processing coords for image %s----------", file_name)
        bad_colony_counter = 0
        too_small_colony_counter = 0
        over_edge_colony_counter = 0
        doublet_colony_counter = 0

        total_colonies_in_image = len(coord_list)    
        temp_coords[file_name] = []                                     # holds the coordinates of colonies that are sampleable
        

        for main_colony_coords in coord_list:
            bad_colony = False

            main_colony_x = float(main_colony_coords[0]) / img_width
            main_colony_y = float(main_colony_coords[1]) / img_height
            main_colony_r = float(main_colony_coords[2]) / img_width

            """ 
            check if the colony is in the petri dish
            if it is, check if it is big enough
            if it is, check if there are any nearby colonies that would make it un-sampleable
            """
            if distance_from_center(main_colony_x, main_colony_y) > petri_dish_roi: 
                bad_colony = True
                over_edge_colony_counter = over_edge_colony_counter + 1 
            elif main_colony_r < min_colony_radius:
                bad_colony = True
                too_small_colony_counter = too_small_colony_counter + 1
            else:
                for neighbor_colony_coords in coord_list: # mmm O(n^2). great.
                    neighbor_colony_x = float(neighbor_colony_coords[0]) / img_width
                    neighbor_colony_y = float(neighbor_colony_coords[1]) / img_height
                    neighbor_colony_r = float(neighbor_colony_coords[2]) / img_width
                    
                    
                    # bool for if the current neighbor is the main colony   
                    neighbor_is_main = neighbor_colony_coords == main_colony_coords 
                    # bool for if the main colony is a doublet (is too close to neighbor)
                    main_is_doublet = distance_between_colonies(main_colony_x, main_colony_y, main_colony_r, neighbor_colony_x, neighbor_colony_y, neighbor_colony_r) < min_colony_dist 

                    if (not neighbor_is_main) and main_is_doublet:
                        bad_colony = True
                        doublet_colony_counter = doublet_colony_counter + 1 
                    

            if (not bad_colony) and (not temp_coords[file_name].__contains__(main_colony_coords)):
                temp_coords[file_name].append(main_colony_coords)
                good_colony_counter = good_colony_counter + 1

            elif bad_colony:
                bad_colony_counter = bad_colony_counter + 1

        logging.info("TOO SMALL:..........%s | DOUBLET:.........%s  | OUTSIDE DISH:............%s " , too_small_colony_counter, doublet_colony_counter, over_edge_colony_counter)
        logging.info("DETECTED:...........%s | BAD:............ %s | GOOD:....................%s", total_colonies_in_image, bad_colony_counter,  len(temp_coords[file_name]))
        # logging.info(" ")

    logging.info("Doublet removal complete. %s colonies can be sampled from!", good_colony_counter)
    # logging.info(" ")
    return temp_coords

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

def remove_extra_colonies(coords):
    '''
    removes colonies from dishes with more than 16 colonies until there are 96 colonies total
    '''
    try:
        # logging.info(" ")
        logging.info("Removing extra colonies...")

        total_num_colonies = 0
        counter_dict = {} # key is file name, value is number of times a colony has been removed from that file

        logging.info("Removing extra colonies...")
        for _, coord_list in coords.items():
            total_num_colonies = total_num_colonies + len(coord_list)
            logging.info("Total number of colonies detected: %s", total_num_colonies)

        while total_num_colonies > 96:
            random_file = random.choice(list(coords.keys()))
            
            # only remove colonies from dishes with more than 
            if (len(coords[random_file]) > 16):
                # Remove a random colony from the random file
                random_colony = random.choice(coords[random_file])
                coords[random_file].remove(random_colony)
                counter_dict[random_file] = counter_dict.get(random_file, 0) + 1
                
                total_num_colonies = 0
                for _, coord_list in coords.items():
                    total_num_colonies = total_num_colonies + len(coord_list)

        logging.info("Removed %s colonies from each of the following files: %s", str(counter_dict.values())[12:-1], str(counter_dict.keys())[10:-1])
        logging.info("Extra colonies removed")
        # logging.info(" ")
        return coords
    except:
        logging.critical("Error removing extra colonies")
        raise RuntimeError



def annotate_images(coords, wells = CONSTANTS.WELLS, annotation_image_input_path = CONSTANTS.ANNOTATION_IMAGE_INPUT_PATH, annotation_output_path = CONSTANTS.ANNOTATION_IMAGE_OUTPUT_PATH, petri_dish_roi = CONSTANTS.PETRI_DISH_ROI, image_height = CONSTANTS.IMG_HEIGHT, image_width = CONSTANTS.IMG_WIDTH):
    '''
    takes the images in the image input path, and: draws circles around the colonies, writes the well the colony is destined for next to each colony
    saves annotated images to annotation output path
    FIXME draws ROI circle around petri dish. remove when
    xy coords are unfucked and camera is centered 
    '''
    # logging.info(" ")
    logging.info("Creating annotated images...")

    well_number_index_counter = 0 # itertes for every colony, used to write well number next to colony
    annotated_images = []

    try:
        if not os.path.exists(annotation_output_path):
            logging.info("Creating annotated image directory: %s", annotation_output_path)
            os.makedirs(annotation_output_path)
        

        # Loop through each image file in the specified folder path
        for file_name, coord_list in coords.items():
            
            image = cv2.imread(os.path.join(annotation_image_input_path, str(file_name) + '.jpg'))
        

            # Open the colony coordinates text file corresponding to the current image

            if len(coord_list) > 0:
                # Iterate over each line in the text file
                for colony_line in coord_list:
                    try:
                        x = int(colony_line[0])
                        y = int(colony_line[1])
                        r = int(colony_line[2])
                        if well_number_index_counter < 96:
                            colony_number = wells[well_number_index_counter]
                            well_number_index_counter = well_number_index_counter + 1
                        else:
                            logging.error("Well number index counter exceeded 96. Please remove extra colonies before generating drive coords")
                            colony_number = "ERR"

                    except Exception as e:
                        logging.error("Error extracting colony number: %s", e)
                        raise RuntimeError("Error extracting colony number: %s", e)


                    # draw circles around colonies, and write colony number next to them
                    try:
                        cv2.circle(image, (x, y), int(r), (0, 0, 0), 2)
                        cv2.putText( image, str(colony_number), (int(x + 30), int(y - 30)), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 1) 
                    except Exception as e:
                        logging.error("Error drawing stuff on and near colonies")
                        raise RuntimeError("Error drawing stuff on and near colonies")


            cv2.circle(image, (int(0.5*image_width),int(0.5*image_height)), int(petri_dish_roi * image_width), (0,255,0), 2)    # HACK:remove when xy coordinates are unfucked. shows where edges of petri dish should be
            annotated_images.extend(image)
            # save_path = os.path.join(annotation_output_path, str(file_name + '.jpg'))
            # logging.info("Saving image with %s colonies marked to %s", len(coord_list), save_path)
            # try:
            #     cv2.imwrite(save_path, image)
            # except Exception as e:
            #     logging.error("Error saving annotated images to: %s", save_path)
            #     raise RuntimeError("Error saving annotated images")

        logging.info("Annotated image creation complete")
        # logging.info(" ")
        return (annotated_images)
    
    except Exception as e:
        logging.critical("An error occured while annotating images: ", e)
        raise RuntimeError("An error occured while annotating images: ", e)

def generate_drive_coords(coords, cam_x = CONSTANTS.CAM_X, cam_y = CONSTANTS.CAM_Y, cam_x_offsets = CONSTANTS.CAM_X_OFFSETS, cam_y_offsets = CONSTANTS.CAM_Y_OFFSETS, img_width = CONSTANTS.IMG_WIDTH, img_height = CONSTANTS.IMG_HEIGHT):
    # logging.info(" ")
    logging.info("Generating drive coords...")

    total_colony_counter = 0 
    dish_offset_index_counter = 0
    drive_coords = []

    for _, coord_list in coords.items():
            total_colony_counter = total_colony_counter + len(coord_list)
            for colony_line in coord_list:
                x = (cam_y_offsets[dish_offset_index_counter] - (cam_x / 2)) + (colony_line[0]/img_width) * cam_x # FIXME THIS IS PROBABLY WRONG
                y = (cam_x_offsets[dish_offset_index_counter] - (cam_y / 2)) + (colony_line[1]/img_height) * cam_y
                drive_coords.extend([x, y])
            dish_offset_index_counter = dish_offset_index_counter + 1
    logging.info("Drive coords generted for %s colonies", total_colony_counter)
    # logging.info(" ")

    if total_colony_counter > 96:
        logging.critical("Error generating drive coords: expected 96 colonies or less, got %s", total_colony_counter)
        raise RuntimeError("Error generating drive coords: expected 96 colonies or less, got %s" % total_colony_counter)

    else:
        return drive_coords