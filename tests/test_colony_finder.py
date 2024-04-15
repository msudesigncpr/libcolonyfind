from libcolonyfind.colony_finder import ColonyFinder
# import pytest
import cv2

def test_colony_finder():
    raw_image_path='../../4-5-images'
    csv_out_path='output\cfu-csv'

    img0 = cv2.imread('4-5-images\p0.jpg')
    img1 = cv2.imread('4-5-images\p1.jpg')
    img2 = cv2.imread('4-5-images\p2.jpg')
    img3 = cv2.imread('4-5-images\p3.jpg')

    cf = ColonyFinder(raw_image_path, csv_out_path, [img0, img1, img2, img3])
    cf.run_full_proc() # process images, create annotated images

    image = cf.get_annot_images()
    for index, image in enumerate(image):
        cv2.imwrite('output\\annotated-images\\' + str(index) + ".jpg", image)

if __name__ == "__main__":
    test_colony_finder()