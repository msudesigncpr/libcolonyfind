from libcolonyfind.colony_finder import ColonyFinder
import pytest

def test_colony_finder():
    image_names = ["P0", "P1", "P2", "P3", "P4", "P5"]
    cf = ColonyFinder(raw_image_path='../../4-5-images', csv_out_path='../../output/cfu-csv', image_names=image_names, annotated_image_output_path='../../output/annotated-images')