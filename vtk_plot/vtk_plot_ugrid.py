"""Function to create a 3D unstructured grid.""" 
import numpy as np
from vtkmodules.vtkCommonCore import vtkPoints  # pylint: disable=E0611
from vtkmodules.vtkCommonDataModel import (vtkUnstructuredGrid,vtkCellArray) # pylint: disable=E0611
from vtk.util.numpy_support import numpy_to_vtk # pylint: disable=E0401,E0611
from vtk import VTK_HEXAHEDRON # pylint: disable=E0611
from .make_vtk_plot import make_vtk_plot

def vtk_plot_ugrid(self,dflag='2D',macroapi=False): #pylint: disable=R0914
    """
    Makes a 3D unstructured grid for visualization

    Parameters:
        dflag (str): problem dimension
        macroapi (bool): flag to indicate data source for plotting

    Returns:
        None.
    """

    vs=self.vs
    h5=self.h5

    if macroapi:
        mesh = h5['MACROAPI MESH']
        print('WARNING: MACROAPI only set up for plotting hexahedrons...')
    else:
        print('Ugrid not set up to plot NASMAT standalone results...')
        return

    if dflag=='2D':
        print('Ugrid not setup for plotting 2D')

    #get nodal coordinates
    points=np.array(mesh['Node Coords'])
    # Create a VTK data array from the NumPy array
    points_data = numpy_to_vtk(num_array=points, deep=True)
    # Set the number of components (3 for 3D points)
    points_data.SetNumberOfComponents(3)
    # Set the data array for the vtkPoints object
    pts = vtkPoints()
    pts.SetData(points_data)

    # Create a mapping function
    nodemap = {node_id: row_number for row_number, node_id in enumerate(mesh['Node Numbers'])}
    map_node_id_to_row_number = np.vectorize(nodemap.get)

    # Apply the mapping function to the element connectivity
    ecmod = map_node_id_to_row_number(mesh['Elements'][:,2:]) #from element connectivity

    #create cell array
    cells = vtkCellArray()
    [cells.InsertNextCell(len(c), c) for c in ecmod] #pylint: disable=W0106

    # Create an unstructured grid
    grid = vtkUnstructuredGrid()
    grid.SetPoints(pts) #set points
    grid.SetCells(VTK_HEXAHEDRON, cells) #set cells

    decknum = numpy_to_vtk(num_array=mesh['Elements'][:,1], deep=True)
    decknum.SetNumberOfComponents(1)
    decknum.SetName("SM-IND")
    grid.GetCellData().AddArray(decknum)

    enum = numpy_to_vtk(num_array=mesh['Elements'][:,0], deep=True)
    enum.SetNumberOfComponents(1)
    enum.SetName("MarcoAPI Element ID")
    grid.GetCellData().AddArray(enum)

    if vs['show_res']:
        res = h5['MACROAPI RESULTS']
        grp=f"Inc={vs['ind']+1}/{vs['var']}"
        cmap={0:0,1:1,2:2,3:4,4:5,5:3}
        h5res = numpy_to_vtk(num_array=res[grp][:,cmap[vs['comp']]], deep=True)
        h5res.SetNumberOfComponents(1)
        h5res.SetName(vs['var'])
        grid.GetCellData().AddArray(h5res)

    self.grid=grid
    make_vtk_plot(self,dflag,macroapi=macroapi)
