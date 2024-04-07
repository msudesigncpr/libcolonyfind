# libmotorctrl

This is a library for controlling the CMMO-ST drive controllers on the
colony-picking robot design project. It provides a `DriveManager` class which
maintains Modbus connections with each of the drives and provides convenience
methods for controlling them. See the [documentation][apidocs] for more
information.

[apidocs]: https://msudesigncpr.github.io/libmotorctrl/libmotorctrl/drive_manager.html

## Getting Started

Usage of a virtual environment is highly recommended.

Install with pip directly from this repository:

```sh
python -m venv .venv
.\.venv\Scripts\activate # Un*x systems: source .venv/bin/activate
pip install "git+https://github.com/msudesigncpr/libmotorctrl.git"
```

All methods provided by this library are provided as coroutines to
facillitate performing tasks on multiple drive controllers
concurrently without interfering with the rest of the process control
code. Please familiarize yourself with [the asyncio
documentation][asyncdocs] (particularly the section on coroutines and
tasks).

[asyncdocs]: https://docs.python.org/3/library/asyncio.html

## Minimal Usage Example

To get started quickly, the following code will initialize, home, move
and shut down the drives in sequence.

```python
import asyncio
from libmotorctrl import DriveManager, DriveTarget

async def main():
    drive_ctrl = DriveManager()
    await drive_ctrl.init_drives()

    await drive_ctrl.home(DriveTarget.DriveZ)
    await drive_ctrl.home(DriveTarget.DriveX)
    await drive_ctrl.home(DriveTarget.DriveY)

    await drive_ctrl.move(150_000, 100_000, 90_000)

    await drive_ctrl.terminate()


if __name__ == "__main__":
    asyncio.run(main())
```
