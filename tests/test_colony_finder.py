from libcolonyfind.colony_finder import ColonyFinder
import pytest

def test_colony_finder():
    image_names = ["P0", "P1", "P2", "P3", "P4", "P5"]
    raw_image_path='../../4-5-images'
    csv_out_path='../../output/cfu-csv'
    annotated_image_output_path='../../output/annotated-images'
    cf = ColonyFinder(image_names, raw_image_path, csv_out_path, annotated_image_output_path)
    coords = cf.run_full_proc() # Process images and return coordinates of colonies