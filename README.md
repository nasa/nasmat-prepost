# NASMAT PrePost: A visualization and analysis tool for the NASMAT

NASMAT PrePost is a suite of standalone tools and a user interface designed to generate, visualize, and analyze data produced for and by the NASMAT software. At its core, NASMAT PrePost is developed using Python 3 and dynamically links to three main open-source tools: VTK (a graphics renderer), QT (a user interface), and PyQT5 (a translator between python and QT's C++ functions). NASMAT PrePost combines these tools (using function calls) to generate its user-interface. NASMAT PrePost can be run in two modes: standalone and through the user interface. In general, more capabilities are present in the standalone code which have not been implemented inside the user interface.

This software is intended and developed for use with NASMAT, which can be separetly requested from the [NASA Software Catalog](https://software.nasa.gov/software/LEW-20650-1).

## Cloning the repository

It is recommended to clone the repository and run NASMAT PrePost from within VS Code. While this is not a hard requirement, it can significantly help with debugging/formatting code.

The public-facing NASMAT PrePost repository can be accessed from the [NASA Github](https://github.com/nasa/nasmat-prepost). From the Explorer panel in VS Code (Ctrl+Shift+E), select "Clone Repository". Enter the following URL path to the repository and choose a directory to clone into:

```bash
https://github.com/nasa/nasmat-prepost.git
```

The primary development respostiory can also be accessed by internal NASA users. Enter the following URL path to the repository and choose a directory to clone into:

```bash
https://gitlab.grc.nasa.gov/trenton.m.ricks/nasmat-prepost.git
```

## Installation with conda

Navigate to the project directory and execute the following commands from an Anaconda prompt to create and activate a new environment:

```bash
conda env create -f environment.yml
conda activate nasmat-prepost
```

Opencv may have problems if installed using conda. See this [issue](https://github.com/opencv/opencv/issues/26352).

## Installation with pip

From a command line, create and activate a new python environment for NASMAT PrePost:

```bash
python -m venv <env_path>/nasmat-prepost
<env_path>/nasmat-prepost/Scripts/activate
```

where <env_path> is the directory where the new environment should be created (not the root directory for the project).

Navigate to the root directory for the project and set up the environment with:

```bash
pip install -r requirements.txt
```

## Running the user interface

### Loading the user interface

The user interface for NASMAT PrePost can be loaded by running [main.py](./main.py). Be sure that the correct python environment is active.

### Setting NASMAT PrePost environment variables

When first executed, NASMAT PrePost creates an environment file in the root directory (named NASMATPrePost.env) that contains various settings for the UI to avoid having to repeatedly change the UI behavior each time it is launched. Additional settings can be added to the Python scripts if desired with the format "KEY=VALUE".

- The following environment variables are available for use:
    1. NASMAT_SOLVER: NASMAT exectuable
    2. NASMAT_SHARED_PATH: path to NASMAT shared libraries
    3. INTEL_PATH: Intel setvars file
    4. INTEL_OPTS: options to pass Intel setvars file
    5. HDF5_PATH: directory containing hdf5 shared libraries
    6. CLEAR_CMD: option to exectute NASMAT from a clean OS environment (TRUE or FALSE)
    7. COLORMAP: integer value to change the default colormap in the UI (not integrated yet)
    8. BACKGROUND_COLOR: three comma-seprated floats to define the RGB values of the UI background
    9. SHOW_AXES: option to hide or show axes by default (TRUE or FALSE)
   10. SHOW_TITLE: option to hide or show RUC title text by default (TRUE or FALSE)

- The first 5 environment variables must be set in order to run NASMAT from within the UI. Those can be set manually in the environment file or automatically by selecting appropriate options under the UI solver menu.

### Common use cases

- Create a new NASMAT input deck
    1. File → New NASMAT Deck... → Blank
    2. Populate fields in each tab as desired
    3. Click Ok

- Open existing NASMAT Deck
    1. File → Open NASMAT Deck...

- Open existing NASMAT results (*.h5)
    1. File → Open NASMAT H5 File...

- Open both NASMAT Deck and NASMAT results (*.h5) file
    1. File → Open NASMAT Deck...
    2. Results → Attach *.h5 file...

- Switching between unit cells and results
    1. On the far right of the user interface, select either the RUC or Results tab. The RUC tab will show the RUCs as represented in the input deck while the Results tab will show all RUCs in the model including those with the same geometry.
    2. Individual items in the table can be selected to view unit cells and their results.
    3. Alternative selection: left clicking a highlighted cell in an RUC will navigate to a lower level RUC at that cell (if present). Right clicking will revert to the previous selection.

- Slicing 3D unit cells
     1. Holding down the alt key will enable handles in each of the coordinate directions that can be dragged to slice the RUC.
     2. Press the "r" key to reset the view [currently glitchy and requires a handle to be slightly moved again]

- Selecting and view NASMAT results
    1. Load NASMAT results contained in NASMAT H5 file.
    2. Select a unit cell of interest.
    3. Verify the Mode pulldown is set to "H5 Arrays".
    4. Select the result of interest (e.g., field or property), the relavant component, and orientation. By default, NASMAT output results are stored in the unit cell coordinate system rather than the material coordinate system.
    5. Use the arrow keys to reverse and advance the increment/time

- Commonly used plot options
    1. Changing/updating the plot range. Updates the range of values for a single plot.
    2. Hiding/showing materials. Pops up a menu for hiding materials in a unit cell model. Useful for visualizing features of interest (e.g., a weave).
    3. Showing material ids. Displace each subvolume's material id (may be slow for larger models).
    4. Showing material orientations. Plots the local material orientation for each subvolume.

- Creating a video from results
    1. Open existing NASMAT results (*.h5)
    2. Select an RUC of interest.
    3. Update the plot range if desired.
    4. File → Save Video...
    5. Enter a FPS value.
    6. Enter the video filename and click Ok.

### Keyboard Shortcuts

- Press '1': resets camera to default view
- Press and hold 'Alt': enables clipping mode to slice through unit cells. While holding, click and drag one of the spherical handles to slice.
- Press 'r': resets clipper. Note: might not refresh grid when pressed. Press 'Alt' and slightly move one of the handles slightly to fix.

### Known limitations of the user interface

- In general, more features can be found in the standalone codes than are fully integrated into the UI.
- Only supports *CONSTITUENTS, CMOD=6,9,14
- Lack of robust error checking with reading NASMAT inputs. It is best to verify that an input deck successfully runs on NASMAT before opening it on NASMAT PrePost.
- Some NASMAT input files that work with NASMAT may give errors when read in NASMAT PrePost due to differences in input file pre-processing.
- Some hard-coding may prevent code from running on Linux or MAC operating systems. All testing to date has been on Windows.
- When using with MacroAPI results, variable names may not match ones used in the NASMAT H5 file. Ensure appropriate variable mapping is defined in the var_map dict inside the [vtk_widget](./vtk_widget.py) init definition.
- When using RUCs in the [new_Dialog UI](./new_Dialog.py), ensure all MSM values are unique. Available RUCs can have duplicate MSM values.
- Subvolume rotations defined in a *.rot file are not available for defining or editing in the UI.
- Due to development priorities, the 2D weave generation capability has not been fully validated.'
- When trying to run [NASMAT](./NASMAT/NASMAT.py) with multiple job inputs, the execution may get hung up. If this happens, run jobs sequentially (see [Example 3](./standalone_examples/example-3.py) for how to set up)

### Editing the user interface

- [*.ui files](./ui) are provided in the distribution and can be edited in either QT Designer or QT Creator. That is preferable to modifying Python code directly.
- For example, if you have a nasmat-prepost conda environment:
    1. Open an Anaconda Prompt.

    2. Type the following commands:

        ```bash
        conda activate nasmat-prepost
        designer
        ```

## Features implemented in standalone Python code, but not in user interface

- [Importing](./file_importer/file_importer.py) a VTU file (e.g., from TexGen, PuMA).
- [Utility function](./util/stackify.py) to create a NASMAT "stack" model (i.e., converting a single 3D unit cell to two unit cells).
- [Plotting NASMAT "stack" models](./vtk_plot/vtk_plot_stacks.py).
- Adding Abaqus-specific mesh/output data to the NASMAT h5 file. Must be done manually. See [Modifying NASMAT h5 files to add MACROAPI data](#modifying-nasmat-h5-files-to-add-macroapi-data).
- [Parameter and expression substitution](./util/sub_param.py) (e.g., for sensitivity studies).
- [Basic *.out file parser](./util/output_parser.py) for automatically getting simple NASMAT outputs.
- These capabilities (with the exception of Abaqus data plotting) are demonstrated in [Standalone Examples](./standalone_examples/):
  - [Example 1](./standalone_examples/example-1.py): reading an existing MAC file, running, plotting results.
  - [Example 2](./standalone_examples/example-2.py): importing a grid (VTU file) of a plain weave RUC, converting to NASMAT format, manually creating a multiscale model, running, and plotting various quantities. Optional logic to convert the weave RUC to stacks.
  - [Example 3](./standalone_examples/example-3.py): utilizing parameterized NASMAT input decks to define and vary quantities of interest.

## Modifying NASMAT h5 files to add MACROAPI data

By default, when running NASMAT with a MACROAPI (i.e., hookups only provided for Abaqus), Abaqus element data are not written to the NASMAT h5 file. To display results for the entire mesh (including built-in materials), those data need to be extracted from an existing Abaqus ODB file and added to NASMAT's h5 output file. Current plotting capability is limited to single integration point elements so appropriate averaging may need to be performed during the extraction phase. The following procedure details the steps required to add Abaqus ODB data to the NASMAT h5 file. Some modification of the provided codes are required based on Abaqus problem setup.

- One-time Abaqus Python environment setup
    1. Using the Abaqus Python exectuable, install h5py (not included by default in Abaqus python environment). E.g.,"C:\SIMULIA\EstProducts\2024\win_b64\tools\SMApy\python3.10\python.exe" -m pip install h5py
    2. See [abaqus-python-addpkg.py](https://github.com/nasa/CompDam_DGD/blob/master/utilities/abaqus-python-addpkg/abaqus-python-addpkg.py) for more information and an alternative approach using conda.
- Updating NASMAT's h5 output file
    1. Modify and run the [extract_abq_data.py](./macroapi_support/extract_abq_data.py) file as required to extract the requested data from an existing Abaqus ODB file. A *.npy file should be produced.
    2. Modify and run the [abaqus_add_h5.py](./macroapi_support/abaqus_add_h5.py) file to input the previously generated *.npy file, create new h5 datasets, and add those to the NASMAT h5 file.

## Submitting bugs or feature requests

Users are encouraged to create an Issue from the [NASMAT PrePost](https://github.com/nasa/nasmat-prepost) project page. When submitting a bug request, attach any input files if relevant. Feature requests are welcome, but implementation will depend on current NASA project demands and personell availability.

## Reference

This [conference presentation](https://ntrs.nasa.gov/citations/20240016540) demonstrates some of the features of NASMAT PrePost and should be cited when referencing the tool.

## Contact

Please report any limitations, bugs, or features requests to Dr. Trenton M. Ricks at <trenton.m.ricks@nasa.gov> or create a Gitub Issue.
