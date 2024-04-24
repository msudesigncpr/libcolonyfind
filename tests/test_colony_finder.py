from libcolonyfind.colony_finder import ColonyFinder
import cv2

def test_colony_finder():
    raw_image_path='C:\\Users\\John Fike\\OneDrive\\Documents\\Visual Studio 2022\\cap\\libcolonyfind\\4-5-images'
    csv_out_path='output\cfu-csv'

    cf = ColonyFinder(raw_image_path, csv_out_path)
    cf.run_full_proc() # process images, create annotated images
    images = cf.annotate_images()
    print(images)

    for image in images:
        cv2.imshow('image', image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    test_colony_finder()