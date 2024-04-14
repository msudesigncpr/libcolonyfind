# libcolonyfind

This is a library for the automatic detection of colonies for the colony-picking robot 
MSU senior design project. This library provides a `ColonyFinder` class that 
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

![#f03c15](https://placehold.co/15x15/f03c15/f03c15.png) WARNING ![#f03c15](https://placehold.co/15x15/f03c15/f03c15.png) 
> excuse me yes may i have your attention for a moment please

[OpenCFU](https://github.com/msudesigncpr/OpenCFU/tree/master) running on WSL is necesary for this library to work.
The path to this instance of OpenCFU will need to be specified in
[constants.py](https://github.com/msudesigncpr/libcolonyfind/blob/5507e8dfbcfe86470950627f8870ba7f2ad7b9e1/src/libcolonyfind/constants.py#L31-L34)



## Minimal Usage Example

To get started quickly, the following code will ingest images and spit out coords to a maximum of 96 colonies in mm offsets from the center of those images.
In the CPR process control code, this happens [here](https://github.com/msudesigncpr/slate-ui/blob/b9b4d9cf43f448a9027532bd028ca4dd8efafabc/src/slate_ui/process_control.py#L218-L225).


```python
from libcolonyfind.colony_finder import ColonyFinder

def main():
    image_names = ["P0", "P1", "P2", "P3", "P4", "P5"]
    raw_image_path='../../some-images'
    csv_out_path='../../output/cfu-csv'
    annotated_image_output_path='../../output/annotated-images'
    cf = ColonyFinder(image_names, raw_image_path, csv_out_path, annotated_image_output_path)
    coords = cf.run_full_proc() # Process images and return coordinates of colonies

if __name__ == "__main__":
    main()
```
