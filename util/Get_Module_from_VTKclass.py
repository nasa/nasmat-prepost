""" 
Helper function for getting vtk module from vtk class name.
AVOID using "import vtk" statements in code!!!
See: https://vtk.org/doc/nightly/html/md__builds_gitlab_kitware_sciviz_ci_Documentation_Doxygen_PythonWrappers.html 
""" #pylint: disable=C0103

from vtkmodules.all import * #pylint: disable=W0401,W0614

def get_module_from_vtkclass(all_classes):
    """
    function to get vtk module from vtk class name

    Parameters:
        None.

    Returns:
        None.
    """

    for c in all_classes:
        print(c)
        print(f"from {c.__module__} import {c.__name__}")

# Define vtk classes to find modules -- add module imports to code where needed
classes=[vtkDataObject,vtkDataSetAttributes] #pylint: disable=E0602
get_module_from_vtkclass(classes)
