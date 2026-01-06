"""Functions to create a 2D or 3D rectilinear grid.""" #pylint: disable=C0103
import numpy as np
from vtkmodules.vtkCommonDataModel import vtkRectilinearGrid # pylint: disable=E0611
from vtkmodules.vtkCommonCore import vtkIntArray,vtkFloatArray # pylint: disable=E0611
from vtk.util.numpy_support import numpy_to_vtk # pylint: disable=E0401,E0611


def set_ori_all(ncells,name,ori):
    """
    Function to initialize array of default orientations (not used, testing routine)

    Parameters:
        ncells (int): number of cells in grid
        name (str): name of 
        ori (str): default orientation
    Returns:
        o (vtkFloatArray): array of orientations for grid
    """
    o=vtkFloatArray()
    o.SetName(name)
    o.SetNumberOfComponents(3)
    o.SetNumberOfTuples(ncells)
    #update orientations below for testing
    #[o.SetTuple3(i,ori[0],ori[1],ori[2]) for i in range(ncells))
    o.SetTuple3(0,0,0,0)
    o.SetTuple3(1,ori[0],ori[1],ori[2])
    o.SetTuple3(2,0,0,0)
    return o


def make_grid_2d_3d(ruc,vmap,dflag):
    """
    Makes a 2D or 3D rectilinear grid for visualization

    Parameters:
        ruc (dict): ruc parameters
        vmap (dict): map to change material numbers
        dflag (str): problem dimension

    Returns:
        grid (vtkRectilinearGrid): RUC grid
    """

    mod=ruc['mod']
    if mod in (102,202) and not dflag:
        dflag='2D'
    elif not dflag:
        dflag='3D'

    if dflag=='2D':
        d = np.array([0.0,1e-6])
    else:
        d=np.cumsum(np.insert(ruc['d'],0,0.0))


    h = np.cumsum(np.insert(ruc['h'],0,0))
    l = np.cumsum(np.insert(ruc['l'],0,0))

    grid = vtkRectilinearGrid()

    if dflag=='2D':
        grid.SetDimensions(ruc['ng']+1,ruc['nb']+1,2)
        grid.SetXCoordinates(numpy_to_vtk(l))
        grid.SetYCoordinates(numpy_to_vtk(h))
        grid.SetZCoordinates(numpy_to_vtk(d))
        mats=ruc['sm'].astype(int).flatten()
        cell_data = numpy_to_vtk(mats)

    elif dflag=='3D':
        grid.SetDimensions(ruc['na']+1,ruc['nb']+1, ruc['ng']+1)
        grid.SetXCoordinates(numpy_to_vtk(d))
        grid.SetYCoordinates(numpy_to_vtk(h))
        grid.SetZCoordinates(numpy_to_vtk(l))
        mats=ruc['sm'].astype(int).ravel()
        cell_data=vtkIntArray()
        for i,mat in enumerate(mats):
            cell_data.InsertValue(i,mat)

    cell_data.SetName('SM-IND')
    cell_data.SetNumberOfComponents(1)
    cell_data.SetNumberOfTuples(grid.GetNumberOfCells())
    grid.GetCellData().AddArray(cell_data)

    if vmap:
        sm_act = np.vectorize(vmap.get)(mats)
        cell_data=vtkIntArray()
        for i, val in enumerate(sm_act):
            cell_data.InsertValue(i, val)

        cell_data.SetName('SM')
        cell_data.SetNumberOfComponents(1)
        cell_data.SetNumberOfTuples(grid.GetNumberOfCells())
        grid.GetCellData().AddArray(cell_data)

    if 'ORI_X1' in ruc.keys():
        ori_x1 = numpy_to_vtk(ruc['ORI_X1'])
        ori_x1.SetName('ORI_X1')
        ori_x1.SetNumberOfComponents(3)
        ori_x1.SetNumberOfTuples(grid.GetNumberOfCells())
        grid.GetCellData().AddArray(ori_x1)

        ori_x1_norm = numpy_to_vtk(ruc['ORI_X1_NORM'])
        ori_x1_norm.SetName('ORI_X1_NORM')
        ori_x1_norm.SetNumberOfComponents(1)
        ori_x1_norm.SetNumberOfTuples(grid.GetNumberOfCells())
        grid.GetCellData().AddArray(ori_x1_norm)

    if 'ORI_X2' in ruc.keys():
        ori_x2 = numpy_to_vtk(ruc['ORI_X2'])
        ori_x2.SetName('ORI_X2')
        ori_x2.SetNumberOfComponents(3)
        ori_x2.SetNumberOfTuples(grid.GetNumberOfCells())
        grid.GetCellData().AddArray(ori_x2)

        ori_x2_norm = numpy_to_vtk(ruc['ORI_X2_NORM'])
        ori_x2_norm.SetName('ORI_X2_NORM')
        ori_x2_norm.SetNumberOfComponents(1)
        ori_x2_norm.SetNumberOfTuples(grid.GetNumberOfCells())
        grid.GetCellData().AddArray(ori_x2_norm)

    if 'ORI_X3' in ruc.keys():
        ori_x3 = numpy_to_vtk(ruc['ORI_X3'])
        ori_x3.SetName('ORI_X3')
        ori_x3.SetNumberOfComponents(3)
        ori_x3.SetNumberOfTuples(grid.GetNumberOfCells())
        grid.GetCellData().AddArray(ori_x3)

        ori_x3_norm = numpy_to_vtk(ruc['ORI_X3_NORM'])
        ori_x3_norm.SetName('ORI_X3_NORM')
        ori_x3_norm.SetNumberOfComponents(1)
        ori_x3_norm.SetNumberOfTuples(grid.GetNumberOfCells())
        grid.GetCellData().AddArray(ori_x3_norm)

    return grid
