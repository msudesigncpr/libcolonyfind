from pathlib import WindowsPath, Path
import subprocess
import logging
import random
import csv
import os
import cv2
from libcolonyfind import constants as CONSTANTS

# TODO: accept an array of image names

# TODO pass thru init


class ColonyFinder:
    def __init__(
        self,
        raw_image_path,
        csv_out_path,
        image_names,
        annotated_image_output_path=None,
    ):
        self.raw_image_path = raw_image_path
        self.csv_out_path = csv_out_path
        self.annotated_image_output_path = annotated_image_output_path

        self.image_names = image_names

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
        coords = self.parse_cfu_csv(self.csv_out_path)
        coords = self.remove_invalid_colonies(coords)
        coords = self.remove_extra_colonies(coords)

        if self.annotated_image_output_path is not None:
            self.annotate_images(
                coords, self.raw_image_path, self.annotated_image_output_path
            )
        baseplate_coords = self.generate_baseplate_coords(coords)
        return baseplate_coords

    def run_cfu(self, raw_image_path, csv_out_path, cfu_path=CONSTANTS.CFU_PATH):
        """
        uses WSL to run the instance of OpenCFU at CONSTANTS.CFU_PATH on images in img_folder_path
        OpenCFU generates .csv files, dumps them in `csv_out_path`
        """

        images_for_cfu_path = Path(raw_image_path).resolve()
        images_for_cfu_wsl_path = images_for_cfu_path.as_posix().replace("C:", "/mnt/c")
        cfu_csv_win_dump_path = Path(csv_out_path).resolve()
        cfu_csv_wsl_dump_path = cfu_csv_win_dump_path.as_posix().replace("C:", "/mnt/c")

        init_dir = os.getcwd()

        try:
            logging.info("Moving to OpenCFU dir...")
            os.chdir(WindowsPath(cfu_path))
        except:
            logging.critical("Error changing directory")
            raise RuntimeError("Error changing directory")

        try:
            for image in os.listdir(images_for_cfu_wsl_path):
                base_image_name = os.path.splitext(os.path.basename(image))[0]
                logging.info("Processing image %s", base_image_name)

                cfu_image_wsl_path = (
                    images_for_cfu_wsl_path + "/" + base_image_name + ".jpg"
                )  # where cfu will look for img
                cfu_coord_wsl_path = (
                    cfu_csv_wsl_dump_path + "/" + base_image_name + ".csv"
                )  # where cfu will place coords to colonies it finds (ex /mnt/c/Users/colon/Downloads/GUI/src/cfu_coords/dish_0.csv)
                print(cfu_image_wsl_path)
                print(cfu_coord_wsl_path)
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
                        ]
                    )  # TODO can I pipe to project dir path?
                    # subprocess.run(['wsl', 'mv', cfu_coord_wsl_path, cfu_csv_wsl_dump_path])
                except:
                    logging.critical("OpenCFU failed to run")
                    raise RuntimeError("OpenCFU failed to run")

            logging.info("CFU processing complete")

        except:
            logging.critical("CFU processing failed, terminating...")
            raise RuntimeError("CFU processing failed, terminating...")
        os.chdir(init_dir)

    def parse_cfu_csv(self, csv_path, gsd_x=CONSTANTS.GSD_X):
        """
        openCFU generates .csv files, which are moved to https://github.com/msudesigncpr/slate-ui/blob/b9b4d9cf43f448a9027532bd028ca4dd8efafabc/src/slate_ui/process_control.py#L218-L224
        This function reads the .csv files, extracts the colony coordinates returns a dict with the file name as the key, and the value as a list of coordinates for each colony in the image
        for ex:

        coords = {


                    'file1': [[x1, y1, r1], [x2, y2, r2], [x3, y3, r3]],


                    'file2': [[x1, y1, r1], [x2, y2, r2], [x3, y3, r3]],


                    'file3': [[x1, y1, r1], [x2, y2, r2], [x3, y3, r3]]


        }
        """
        logging.info("Parsing CFU CSVs...")

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

                    # loop thru every row in the csv file, extract the x, y, and r values, and throw them in the coords dict
                    for row in data:
                        x = float(row[1])
                        y = float(row[2])
                        r = float(row[7])

                        mm_coords = self.baseplate_coord_transform(x, y)
                        mm_coords.extend([r * gsd_x])

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
        img_height=CONSTANTS.IMG_HEIGHT,
        img_width=CONSTANTS.IMG_WIDTH,
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

        temp_coords = {}
        good_colony_counter = 0

        for image_name, coord_list in coords.items():
            logging.info(
                "----------Processing coords for image %s----------", image_name
            )
            bad_colony_counter = 0
            too_small_colony_counter = 0
            over_edge_colony_counter = 0
            doublet_colony_counter = 0

            total_colonies_in_image = len(coord_list)
            temp_coords[image_name] = (
                []
            )  # holds the coordinates of colonies that are valid
            out_of_bounds_colony_counter = 0

            petri_dish_counter = 0

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
                elif main_colony_r < min_colony_radius:
                    bad_colony = True
                    too_small_colony_counter = too_small_colony_counter + 1
                else:
                    for neighbor_colony_coords in coord_list:  # mmm O(n^2). great.
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

                        main_is_out_bounds = (
                            self.baseplate_coord_transform(
                                main_colony_x, main_colony_y
                            )[1]
                            < -27.77
                        ) and (
                            petri_dish_counter == 0 or petri_dish_counter == 1
                        )  # TODO: Make petri dish counter numbers constants
                        print(
                            "Colony is out of bounds: ",
                            self.baseplate_coord_transform(
                                main_colony_x, main_colony_y
                            )[1]
                            > 27.77,
                        )

                        if main_is_out_bounds:
                            bad_colony = True
                            out_of_bounds_colony_counter = (
                                out_of_bounds_colony_counter + 1
                            )
                        elif (not neighbor_is_main) and main_is_doublet:
                            bad_colony = True
                            doublet_colony_counter = doublet_colony_counter + 1

                if (not bad_colony) and (
                    not temp_coords[image_name].__contains__(main_colony_coords)
                ):
                    temp_coords[image_name].append(main_colony_coords)
                    good_colony_counter = good_colony_counter + 1

                elif bad_colony:
                    bad_colony_counter = bad_colony_counter + 1

            logging.info(
                "TOO SMALL:..........%s | DOUBLET:.........%s  | OUTSIDE DISH:............%s ",
                too_small_colony_counter,
                doublet_colony_counter,
                over_edge_colony_counter,
            )
            logging.info(
                "DETECTED:...........%s | BAD:............ %s | GOOD:....................%s",
                total_colonies_in_image,
                bad_colony_counter,
                len(temp_coords[image_name]),
            )
            print("out of bounds counter:", out_of_bounds_colony_counter)

        logging.info(
            "Doublet removal complete. %s colonies can be sampled from!",
            good_colony_counter,
        )
        # logging.info(" ")
        return temp_coords

    def distance_from_center(self, x0, y0):
        x_dist = abs(x0 - 0.5) ** 2
        y_dist = abs(y0 - 0.5) ** 2
        distance = (x_dist + y_dist) ** 0.5
        return distance

    def distance_between_colonies(self, x0, y0, r0, x1, y1, r1):
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

        x = ((x - center_x) / img_width) * gsd_x  # FIXME THIS IS PROBABLY WRONG
        y = ((y - center_y) / img_height) * gsd_y

        return [x, y]

    def remove_extra_colonies(self, coords):
        """
        removes colonies from coordinate dict until there are 96 or fewer colonies
        """
        try:
            logging.info("Removing extra colonies...")

            total_num_colonies = 0
            for _, coord_list in coords.items():
                total_num_colonies = total_num_colonies + len(coord_list)
            logging.info("Working with %s colonies", len(coord_list))

            counter_dict = (
                {}
            )  # key is file name, value is number of times a colony has been removed from that file
            temp_dict = {
                image_name: [] for image_name in coords.keys()
            }  # copy keys from coords to temp_dict but not the values
            num_colonies_to_sample = 0

            if total_num_colonies > 96:
                while num_colonies_to_sample < 96:
                    for image_name, coord_list in coords.items():
                        if (
                            len(coord_list) > 0
                        ):  # TODO: if the coord is in the two petri dishes next to the bar and they are beyond some limit, don't sample them
                            random_sample = random.sample(coord_list, 1)
                            temp_dict[image_name].append(random_sample)
                            coord_list = [
                                coord
                                for coord in coord_list
                                if coord not in random_sample
                            ]
                            num_colonies_to_sample = num_colonies_to_sample + 1
                            counter_dict[image_name] = (
                                counter_dict.get(image_name, 0) + 1
                            )
                            if len(coord_list) == 0:
                                logging.info(
                                    "All colonies in %s will be sampled from",
                                    image_name,
                                )

            coords = temp_dict

            logging.info(
                "Removed %s colonies from each of the following files: %s",
                str(counter_dict.values())[12:-1],
                str(counter_dict.keys())[10:-1],
            )
            logging.info("Extra colonies removed")
            return coords
        except Exception as e:
            logging.critical("Error removing extra colonies: ", e)
            raise RuntimeError("Error removing extra colonies: ", e)

    def annotate_images(
        self,
        coords,
        annotation_image_input_path,
        annotation_output_path,
        wells=CONSTANTS.WELLS,
        image_height=CONSTANTS.IMG_HEIGHT,
        image_width=CONSTANTS.IMG_WIDTH,
        petri_dish_roi=CONSTANTS.PETRI_DISH_ROI,
        min_colony_radius=CONSTANTS.MIN_COLONY_RADIUS,
        gsd_x=CONSTANTS.GSD_X,
        gsd_y=CONSTANTS.GSD_Y,
    ):
        """
        takes the images in the image input path, and: draws circles around the colonies, writes the well the colony is destined for next to each colony
        saves annotated images to annotation output path
        FIXME draws ROI circle around petri dish. remove when
        xy coords are unfucked and camera is centered
        """
        # logging.info(" ")
        logging.info("Creating annotated images...")

        well_number_index_counter = (
            0  # itertes for every colony, used to write well number next to colony
        )
        annotated_images = []

        try:
            if not os.path.exists(annotation_output_path):
                try:
                    logging.info(
                        "Creating annotated image directory: %s", annotation_output_path
                    )
                    os.makedirs(annotation_output_path)
                except Exception as e:
                    logging.info(
                        "Error creating annotation image output directory: ", e
                    )
                    raise RuntimeError(
                        "Error creating annotationt image output diretory: ", e
                    )

            logging.info("Annotated images will be saved to %s", annotation_output_path)

            # Loop through each image file in the specified folder path
            for image_name, coord_list in coords.items():
                logging.info("Creating annotations for %s", image_name)
                image = cv2.imread(
                    os.path.join(annotation_image_input_path, str(image_name) + ".jpg")
                )

                # Open the colony coordinates text file corresponding to the current image

                if len(coord_list) > 0:
                    # Iterate over each line in the text file
                    for colony_coord in coord_list:
                        try:
                            x = int(colony_coord[0])
                            y = int(colony_coord[1])
                            r = int(colony_coord[2])
                            if well_number_index_counter < 96:
                                colony_number = wells[well_number_index_counter]
                                well_number_index_counter = (
                                    well_number_index_counter + 1
                                )
                            else:
                                logging.error(
                                    "Well number index counter exceeded 96. Please remove extra colonies before generating baseplate coords"
                                )
                                colony_number = "ERR"

                        except Exception as e:
                            logging.error("Error extracting colony number: %s", e)
                            raise RuntimeError("Error extracting colony coords: %s", e)

                        # draw circles around colonies, and write colony number next to them
                        try:
                            cv2.circle(image, (x, y), int(r), (0, 0, 0), 2)
                            cv2.rectangle(
                                image,
                                (int(x - 0.5 * gsd_x), int(y - 0.5 * gsd_y)),
                                (int(x + 0.5 * gsd_x), int(y + 0.5 * gsd_y)),
                                (0, 0, 0),
                                2,
                            )  # FIXME
                            cv2.putText(
                                image,
                                str(colony_number),
                                (int(x + 30), int(y - 30)),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                2,
                                (0, 0, 0),
                                1,
                            )
                        except Exception as e:
                            logging.error("Error drawing annotations")
                            raise RuntimeError("Error drawing annotations")

                cv2.circle(
                    image,
                    (int(0.5 * image_width), int(0.5 * image_height)),
                    int(petri_dish_roi * image_width),
                    (0, 255, 0),
                    2,
                )
                annotated_images.extend(image)

                save_path = os.path.join(annotation_output_path, image_name + ".jpg")
                logging.info("Saving annotated image to: %s", save_path)
                cv2.imwrite(save_path, image)

            logging.info("Annotated image creation complete")

            return annotated_images

        except Exception as e:
            logging.critical("An error occured while annotating images: ", e)
            raise RuntimeError("An error occured while annotating images: ", e)

    def generate_baseplate_coords(self, coords, wells=CONSTANTS.WELLS):
        logging.info("Generating baseplate coords...")
        try:
            total_colony_counter = 0
            well_counter = 0

            for _, coord_list in coords.items():
                for colony_coord in coord_list:
                    print(colony_coord)

                    colony_coord = colony_coord[:-1]  # remove radius from colony coord
                    colony_coord = self.baseplate_coord_transform(
                        colony_coord[0], colony_coord[1]
                    )

                    print(
                        "Well: ",
                        wells[well_counter],
                        "for colony coords: ",
                        colony_coord,
                    )
                    well_counter = well_counter + 1

            if total_colony_counter > 96:
                logging.warning(
                    "Error generating baseplate coords: expected 96 colonies or less, got %s",
                    total_colony_counter,
                )
                pass

            else:
                logging.info(
                    "baseplate coords generted for %s colonies", total_colony_counter
                )
                return coords

        except Exception as e:
            logging.critical("Error generating baseplate coords: ", e)
            raise RuntimeError("Error generating baseplate coords: ", e)
