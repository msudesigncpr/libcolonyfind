# libcolonyfind

This is a library for the automatic detection of colonies for the colony-picking robot 
MSU senior design project. This library provides a single function `find_colonies()` that 
returns a dict containing coordinates to colonies that are valid for sampling. If a path 
for annotated images to be saved to is supplied, annotated images will be created and saved. 
See the apidocs for more information. 

Along with detecting colonies, this library also handles:
 - The creation of annotated images
 - The removal of "extra" colonies
 - The removal of out-of-bounds colonies

apidocs are coming...
api docs for coord system info

## Getting Started

Usage of a virtual environment is highly recommended.

Install with pip directly from this repository:

```sh
python -m venv .venv
.\.venv\Scripts\activate # Un*x systems: source .venv/bin/activate
pip install "git+https://github.com/msudesigncpr/libcolonyfind.git"
```

> [!warning] **WARNING**
> OpenCFU running on WSL is necesary for this library to work.
> libcolonyfind WILL NOT WORK if this is not the case!
> The path to this instance of OpenCFU will need to be specified in
> [constants.py](src/libcolonyfind/constants.py)
TODO: fork https://github.com/qgeissmann/OpenCFU and link here

## Minimal Usage Example

To get started quickly, the following code will 

```python
from libcolonyfind import find_colonies

def main():
        output_dir = "./output"      
        
        csv_out_dir = Path(output_dir / "02_csv_data")     # OpenCFU finds colonies within images, those coords are placed here
        annotated_image_dir = Path(output_dir / "03_annotated") 
        csv_out_dir.mkdir()
        annotated_image_dir.mkdir()
        raw_baseplate_coords_dict = find_colonies(
            self.raw_image_path, self.csv_out_dir, self.annotated_image_dir
        )  # saves annotated images to annotated_image_dir, returns coords to colonies (api docs for coord system info)

if __name__ == "__main__":
    main()
```
