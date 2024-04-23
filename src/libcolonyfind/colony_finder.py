from pathlib import WindowsPath, Path
import subprocess
import logging
import random
import numpy as np
import csv
import os
import cv2
from libcolonyfind import constants as CONSTANTS


class ColonyFinder:
    def __init__(
        self,
        raw_image_path,
        csv_out_path,
    ):
        self.raw_image_path = raw_image_path
        self.csv_out_path = csv_out_path

        """
        array of images to annotate. If None, will not annotate images
        """
        """
        array of annotated images
        """

        self.raw_coords = {}
        self.valid_coords = {}
        self.final_coords = {}

        logging.basicConfig(
            format="%(asctime)s: %(message)s",
            level=logging.INFO,
            datefmt="%H:%M:%S",
        )

    def run_full_proc(self):
        self.run_cfu(self.raw_image_path, self.csv_out_path)
        self.raw_coords = self.parse_cfu_csv(self.csv_out_path)
        self.valid_coords = self.remove_invalid_colonies(self.raw_coords)
        self.final_coords = self.remove_extra_colonies(self.valid_coords)

    def get_annot_images(self):
        return self.annotate_images()

    def get_coords(self):
        return self.final_coords

    def run_cfu(self, raw_image_path, csv_out_path, cfu_path=CONSTANTS.CFU_PATH):
        """
        Uses WSL to run the instance of OpenCFU at CONSTANTS.CFU_PATH on images in img_folder_path
        OpenCFU generates .csv files, dumps them in `csv_out_path`
        Those are then parsed by parse_cfu_csv
        """

        images_for_cfu_path = Path(raw_image_path).resolve()
        images_for_cfu_wsl_path = images_for_cfu_path.as_posix().replace("C:", "/mnt/c")
        cfu_csv_win_dump_path = Path(csv_out_path).resolve()
        cfu_csv_wsl_dump_path = cfu_csv_win_dump_path.as_posix().replace("C:", "/mnt/c")

        if len(os.listdir(images_for_cfu_path)) == 0:
            logging.error("!!!!!!!!!!!!!!!!!!!!! No images found in %s !!!!!!!!!!!!!!!!!!!!", images_for_cfu_path)

        init_dir = os.getcwd()

        try:
            logging.info("Moving to OpenCFU dir...")
            os.chdir(WindowsPath(cfu_path))
        except:
            logging.critical("Error changing directory")
            raise RuntimeError("Error changing directory")

        try:
            for image in os.listdir(images_for_cfu_path):
                base_image_name = os.path.splitext(os.path.basename(image))[0]
                logging.info("Processing image %s", base_image_name)

                cfu_image_wsl_path = (
                    images_for_cfu_wsl_path + "/" + base_image_name + ".jpg"
                )  # where cfu will look for img
                cfu_coord_wsl_path = (
                    cfu_csv_wsl_dump_path + "/" + base_image_name + ".csv"
                )  # where cfu will place coords to colonies it finds (ex /mnt/c/Users/colon/Downloads/GUI/src/cfu_coords/dish_0.csv)
                try:
                    # run cfu on images and move resultant coords to csv dumppath
                    subprocess.run(
                        [
                            "wsl",
                            "./opencfu",
                            "-i",
                            cfu_image_wsl_path,
                            ">",
                            cfu_coord_wsl_path,
                        ], creationflags=subprocess.CREATE_NO_WINDOW, check=True
                    )

                except:
                    logging.critical("OpenCFU failed to run")
                    raise RuntimeError("OpenCFU failed to run")

            logging.info("CFU processing complete")

        except:
            logging.critical("CFU processing failed, terminating...")
            raise RuntimeError("CFU processing failed, terminating...")
        os.chdir(init_dir)

    def parse_cfu_csv(self, csv_path):
        """
        openCFU generates .csv files, which are moved to where the process control sends them. This happens
        [here](https://github.com/msudesigncpr/slate-ui/blob/b9b4d9cf43f448a9027532bd028ca4dd8efafabc/src/slate_ui/process_control.py#L218-L224)
        This function reads the .csv files, extracts the colony coordinates, and returns a dict with the file names as the keys, and coordinates as the values.
        These coords are in mm offsets from the center of the image. This is done using the baseplate_coord_transform function.
        Check out the constants.py docs for more info on the conversion factors used.

        for ex:

        coords = {


                    'file1': [[x1, y1, r1], [x2, y2, r2], [x3, y3, r3]],


                    'file2': [[x1, y1, r1], [x2, y2, r2], [x3, y3, r3]],


                    'file3': [[x1, y1, r1], [x2, y2, r2], [x3, y3, r3]]


        }
        """
        logging.info("Parsing CFU CSVs...")

        if len(os.listdir(csv_path)) == 0:
            logging.error("!!!!!!!!!!!!!!!!!!!!! No CSVs found in %s !!!!!!!!!!!!!!!!!!!!", csv_path)

        coords = {}
        offset_index = 0

        try:
            for csv_file in os.listdir(csv_path):
                temp = []
                base_image_name = os.path.splitext(os.path.basename(csv_file))[0]
                logging.info("Processing CFU CSV %s", base_image_name)

                # read in csvs
                with open(os.path.join(csv_path, csv_file), "r", newline="") as infile:
                    reader = csv.reader(infile)

                    rows = list(reader)
                    data = rows[1:]

                    # loop thru every row in the csv file, extract the x, y, and r values, translate to mm offset from center, and throw them in the coords dict
                    for row in data:
                        x = float(row[1])
                        y = float(row[2])
                        r = float(row[7])

                        mm_coords = self.baseplate_coord_transform(x, y, r)

                        temp.append(mm_coords)

                coords[base_image_name] = temp
                offset_index = offset_index + 1

            logging.info("CFU CSV procecssing complete")
            return coords

        except Exception as e:
            logging.critical("CFU CSV processing failed: %s", e)  # TODO fix logging
            raise RuntimeError("CFU CSV processing failed: %s", e)

    def remove_invalid_colonies(
        self,
        coords,
        petri_dish_roi=CONSTANTS.PETRI_DISH_ROI,
        min_colony_dist=CONSTANTS.MIN_COLONY_DISTANCE,
        min_colony_radius=CONSTANTS.MIN_COLONY_RADIUS,
        x_limit_min=CONSTANTS.XLIMIT_MIN,
    ):
        """
        Processes coord dict and removes colonies that are:
        - Too close to the edge of the petri dish (CONSTANTS.PETRI_DISH_ROI)
        - Too close together (CONSTANTS.MIN_COLONY_DISTANCE)
        - Too small (CONSTANTS.MIN_COLONY_RADIUS)
        - Too close to the x-axis origin to be sampled
            - The camera mount sticks out towards the negative-x direction. If there are colonies on the edge of the petri dish nearest to the x-axis origin, they cannot be picked, as the camera would be obliterated by the 8020 frame.
        """
        logging.info("Removing invalid colonies...")

        if len(coords) == 0:
            logging.error("!!!!!!!!!!!!!!!!!!!!! No colonies found in coords !!!!!!!!!!!!!!!!!!!!")

        temp_coords = {}

        petri_dish_counter = 0
        good_colony_counter = 0

        for image_name, coord_list in coords.items():
            logging.info(
                "----------Processing coords for image %s----------", image_name
            )
            bad_colony_counter = 0
            too_small_colony_counter = 0
            over_edge_colony_counter = 0
            doublet_colony_counter = 0
            out_of_bounds_colony_counter = 0

            total_colonies_in_image = len(coord_list)
            temp_coords[
                image_name
            ] = []  # holds the coordinates of colonies that are valid

            for main_colony_coords in coord_list:
                bad_colony = False

                main_colony_x = float(main_colony_coords[0])
                main_colony_y = float(main_colony_coords[1])
                main_colony_r = float(main_colony_coords[2])

                if (
                    self.distance_from_center(main_colony_x, main_colony_y)
                    > petri_dish_roi
                ): 
                    bad_colony = True
                    over_edge_colony_counter = over_edge_colony_counter + 1

                else:
                    for neighbor_colony_coords in coord_list:  # mmm. stupid code.
                        neighbor_colony_x = float(neighbor_colony_coords[0])
                        neighbor_colony_y = float(neighbor_colony_coords[1])
                        neighbor_colony_r = float(neighbor_colony_coords[2])

                        # bool for if the current neighbor is the main colony
                        neighbor_is_main = neighbor_colony_coords == main_colony_coords
                        # bool for if the main colony is a doublet (is too close to neighbor)
                        main_is_doublet = (
                            self.distance_between_colonies(
                                main_colony_x,
                                main_colony_y,
                                main_colony_r,
                                neighbor_colony_x,
                                neighbor_colony_y,
                                neighbor_colony_r,
                            )
                            < min_colony_dist
                        )

                        main_is_out_bounds = (main_colony_x < x_limit_min) and (
                            petri_dish_counter == 0 or petri_dish_counter == 1
                        )


                        if (not neighbor_is_main) and main_is_doublet:
                            bad_colony = True
                            doublet_colony_counter = doublet_colony_counter + 1

                        elif (not neighbor_is_main) and (main_colony_r < min_colony_radius):
                            bad_colony = True
                            too_small_colony_counter = too_small_colony_counter + 1

                        elif (not neighbor_is_main) and main_is_out_bounds:
                            bad_colony = True
                            out_of_bounds_colony_counter = (
                                out_of_bounds_colony_counter + 1
                            )

                if (not bad_colony) and (
                    not temp_coords[image_name].__contains__(main_colony_coords)
                ):
                    temp_coords[image_name].append(main_colony_coords)
                    good_colony_counter = good_colony_counter + 1

                elif bad_colony:
                    bad_colony_counter = bad_colony_counter + 1
                    temp_coords[image_name] = [
                        coord
                        for coord in temp_coords[image_name]
                        if coord != main_colony_coords
                    ]

            logging.info(
                "TOO SMALL:..........%s | DOUBLET:.........%s  | OUTSIDE DISH:............%s | OOB:....................%s",
                too_small_colony_counter,
                doublet_colony_counter,
                over_edge_colony_counter,
                out_of_bounds_colony_counter,
            )
            logging.info(
                "DETECTED:...........%s | REMOVED:............ %s | REMAIN:....................%s",
                total_colonies_in_image,
                bad_colony_counter,
                len(temp_coords[image_name]),
            )
            petri_dish_counter += 1

        logging.info(
            "Invalid colony removal complete. %s colonies can be sampled from!",
            good_colony_counter,
        )
        return temp_coords

    def distance_from_center(self, x0, y0):
        """
        returns the distance from the center of the image to a given point
        """
        x_dist = abs(x0 - 0.5) ** 2
        y_dist = abs(y0 - 0.5) ** 2
        distance = (x_dist + y_dist) ** 0.5
        return distance

    def distance_between_colonies(self, x0, y0, r0, x1, y1, r1):
        """
        returns the distance between two colonies. If the colonies are overlapping, returns -1
        """
        x_dist = abs(x0 - x1) ** 2
        y_dist = abs(y0 - y1) ** 2
        distance = (x_dist + y_dist) ** 0.5
        # check if they are overlapping. return -1 if they are
        if distance > (r0 + r1):
            return distance - (r0 + r1)
        else:
            return -1

    def baseplate_coord_transform(
        self,
        x,
        y,
        r,
        gsd_x=CONSTANTS.GSD_X,
        gsd_y=CONSTANTS.GSD_Y,
        img_width=CONSTANTS.IMG_WIDTH,
        img_height=CONSTANTS.IMG_HEIGHT,
    ):
        """
        turns pixel coorinates to mm offsets from the center of the image
        """
        center_x = 0.5 * img_width
        center_y = 0.5 * img_height

        x = ((x - center_x) / img_width) * gsd_x
        y = ((y - center_y) / img_height) * gsd_y
        r = r * (gsd_x / img_width)

        return [x, y, r]

    def inv_baseplate_coord_transform(
        self,
        x,
        y,
        r,
        gsd_x=CONSTANTS.GSD_X,
        gsd_y=CONSTANTS.GSD_Y,
        img_width=CONSTANTS.IMG_WIDTH,
        img_height=CONSTANTS.IMG_HEIGHT,
    ):
        """
        turns mm offsets from the center of the image to pixel coordinates
        """
        center_x = 0.5 * img_width
        center_y = 0.5 * img_height

        x = ((x / gsd_x) * img_width) + center_x
        y = ((y / gsd_y) * img_height) + center_y
        r = r * (img_width / gsd_x)

        return [x, y, r]

    def remove_extra_colonies(self, coords):
        """
        Randomly removes colonies from coordinate dict if there are more than 96 total valid colonies
        """
        logging.info("Removing extra colonies...")
        try:
            # num_colonies_to_sample = 0
            total_num_colonies = 0
            counter_dict = {}
            num_colonies_to_sample = 0

            for _, coord_list in coords.items():
                total_num_colonies = total_num_colonies + len(coord_list)
            logging.info("Working with %s colonies", total_num_colonies)

            # copy keys from coords to temp_dict but not the values
            temp_dict = {image_name: [] for image_name in coords.keys()}

            if total_num_colonies > 96:
                while num_colonies_to_sample < 96:
                    for image_name, coord_list in coords.items():
                        if len(coord_list) > 0:
                            random_sample = random.sample(coord_list, 1)
                            if not temp_dict[image_name].__contains__(random_sample[0]):
                                temp_dict[image_name].extend(random_sample)
                                coord_list = [
                                    coord
                                    for coord in coord_list
                                    if coord not in random_sample
                                ]
                                print("Num colonies to sample: ", num_colonies_to_sample)
                                num_colonies_to_sample += 1
                                counter_dict[image_name] = (
                                    counter_dict.get(image_name, 0) + 1
                                )
                coords = temp_dict

                logging.info("%s colonies were removed. Returning %s colonies", total_num_colonies - num_colonies_to_sample, num_colonies_to_sample)

                logging.info(
                    "%s samples come from the following files: %s",
                    str(counter_dict.values())[12:-1],
                    str(counter_dict.keys())[10:-1],
                )
                logging.info("Extra colonies removed")
            else:
                logging.info("No extra colonies to remove. Returning original coords.")
            return coords

        except Exception as e:
            logging.critical("Error removing extra colonies: ", e)
            raise RuntimeError("Error removing extra colonies: ", e)

    def annotate_images(
        self,
        wells=CONSTANTS.WELLS,
        image_height=CONSTANTS.IMG_HEIGHT,
        image_width=CONSTANTS.IMG_WIDTH,
        petri_dish_roi=CONSTANTS.PETRI_DISH_ROI,
        gsd_x=CONSTANTS.GSD_X,
    ):
        """
        takes the images in the image input path, and:
        - draws circles around the colonies
        - writes the well the colony is destined for next to each colony
        - draws a circle around the colony 
        - draws a circle of the same radius as CONSTANTS.MIN_COLONY_RADIUS in the center of the colony
        text and circles are colored randomly, so that the viewer can see which colonies are being put in what well

        - **Returns** a dict of annotated images, with the image name as the key, and the annotated image as the value
        """
        # logging.info(" ")
        logging.info("Creating annotated images...")

        well_number_index_counter = (
            0  # itertes for every colony, used to write well number next to colony
        )
        annotated_images = {}
        coords = self.final_coords
        # coords = self.valid_coords

        try:
            # Loop through each image file in the specified folder path
            for image_name, coord_list in coords.items():
                logging.info("Creating annotations for %s", image_name)

                print(os.path.join(self.raw_image_path, image_name + ".jpg"))
                image = cv2.imread(
                    os.path.join(self.raw_image_path, image_name + ".jpg")
                )

                if len(coord_list) > 0:
                    for colony_coord in coord_list:
                        try:
                            x = colony_coord[0]
                            y = colony_coord[1]
                            r = colony_coord[2]
                            x, y, r = map(
                                int, self.inv_baseplate_coord_transform(x, y, r)
                            )

                            if well_number_index_counter < 96:
                                colony_number = wells[well_number_index_counter]
                                well_number_index_counter = (
                                    well_number_index_counter + 1
                                )
                            else:
                                logging.error(
                                    "Tried to create annotations for over 96 colonies. Please remove extra colonies before beginning sampling."
                                )
                                colony_number = "ERR"

                        except Exception as e:
                            logging.error("Error extracting colony number: %s", e)
                            raise RuntimeError("Error extracting colony coords: %s", e)

                        # draw circles around colonies, and write colony number next to them
                        try:
                            random_color = (
                                random.randint(0, 155),
                                random.randint(0, 155),
                                random.randint(0, 155),
                            )
                            cv2.circle(image, (x, y), int(r), random_color, 2)
                            cv2.circle(
                                image,
                                (x, y),
                                int(
                                    CONSTANTS.MIN_COLONY_DISTANCE 
                                    * (CONSTANTS.IMG_WIDTH / CONSTANTS.GSD_X)
                                ),
                                random_color,
                                1,
                            )
                            cv2.circle(image, (x, y), 1, random_color, 1)
                            cv2.putText(
                                image,
                                str(colony_number),
                                (int(x + 25), int(y - 25)),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                2,
                                random_color,
                                3,
                            )
                            # draw box around text
                            if len(colony_number) == 3:
                                x_box_offset = 150
                            else:
                                x_box_offset = 110
                            cv2.rectangle(
                                image,
                                (int(x + 19), int(y - 19)),
                                (int(x + x_box_offset), int(y - 75)),
                                random_color,
                                3,
                            )

                        except Exception as e:
                            logging.error("Error drawing annotations")
                            raise RuntimeError("Error drawing annotations")

                cv2.circle(
                    image,
                    (int(0.5 * image_width), int(0.5 * image_height)),
                    int(petri_dish_roi * image_width / gsd_x),
                    (0, 255, 0),
                    2,
                )

                xlim_col = int(
                    CONSTANTS.XLIMIT_MIN * (CONSTANTS.IMG_WIDTH / CONSTANTS.GSD_X)
                )
                xlim_col = int(xlim_col + (image_width / 2))
                cv2.line(
                    image,
                    (xlim_col, 0),
                    (xlim_col, CONSTANTS.IMG_HEIGHT),
                    (0, 255, 0),
                    2,
                )
                annotated_images[image_name] = image

                print("Annotated image created")

                logging.info(
                    "Annotations for %s with %s colonies complete",
                    image_name,
                    len(coord_list),
                )

            logging.info("Annotated image creation complete")

            return annotated_images

        except Exception as e:
            logging.critical("An error occured while annotating images: ", e)
            raise RuntimeError("An error occured while annotating images: ", e)
