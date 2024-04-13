# libcolonyfind

This is a library for the automatic detection of colonies for the colony-picking robot 
MSU senior design project. This library provides a single function `find_colonies()` that 
returns coordinates to colonies within an image valid for sampling.
See the [documentation][apidocs] for more information. 

Along with detecting colonies, this library also handles:
 - The creation of annotated images
 - The removal of "extra" colonies
 - The removal of out-of-bounds colonies
 - Translation of pixel coordinates to mm offsets

[apidocs]: https://msudesigncpr.github.io/libcolonyfind/libcolonyfind/colony_finder.html

## Getting Started

Usage of a virtual environment is highly recommended.

Install with pip directly from this repository:

```sh
python -m venv .venv
.\.venv\Scripts\activate 
pip install "git+https://github.com/msudesigncpr/libcolonyfind.git"
```

> <font color="red">WARNING</font>
>
> [OpenCFU](https://github.com/msudesigncpr/OpenCFU/tree/master) running on WSL is necesary for this library to work.
> The path to this instance of OpenCFU will need to be specified in
> [constants.py](https://github.com/msudesigncpr/libcolonyfind/blob/5507e8dfbcfe86470950627f8870ba7f2ad7b9e1/src/libcolonyfind/constants.py#L31-L34)


## Minimal Usage Example

To get started quickly, the following code will ingest 

```python
from libcolonyfind import find_colonies

def main():
        raw_image_path = "./raw_images" # Folder containing images of petri dishes
        output_dir = "./output"      
        
        csv_out_dir = Path(output_dir / "02_csv_data")     # OpenCFU finds colonies within images, those coords are placed here
        annotated_image_dir = Path(output_dir / "03_annotated") 
        csv_out_dir.mkdir()
        annotated_image_dir.mkdir()
        raw_baseplate_coords_dict = find_colonies(
            raw_image_path, csv_out_dir, annotated_image_dir
        )  # saves annotated images to annotated_image_dir, returns coords to colonies (api docs for coord system info)

if __name__ == "__main__":
    main()
```
