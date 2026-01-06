"""Function to scale a grid.""" #pylint: disable=C0103
from vtkmodules.vtkCommonTransforms import vtkTransform # pylint: disable=E0611
from vtkmodules.vtkFiltersGeneral import vtkTransformFilter # pylint: disable=E0611

def scale_grid(grid,dims):
    """
    Function scale a grid, primarily for stack plotting

    Parameters:
        grid (vtkRectilinearGrid): input grid prior to scaling
        dims (list): 3 floats used to determine scale factors
    Returns:
        o (vtkStructuredGrid): output grid after scaling
    """
    b=list(grid.GetBounds())
    extents=[b[5]-b[4],b[3]-b[2],b[1]-b[0]] #asssumes points may not start at origin

    sf = [dims[i]/extents[i] for i in range(3)]
    # sf = [1.0 for i in range(3)] #maintain for debugging

    transform = vtkTransform()
    transform.Scale(sf)
    transform_filter = vtkTransformFilter()
    transform_filter.SetInputData(grid)
    transform_filter.SetTransform(transform)
    transform_filter.Update()

    return transform_filter.GetOutput()
