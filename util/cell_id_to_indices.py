"""file containing function to convert vtk cell ids to vtk ruc indices """
from vtkmodules.vtkCommonDataModel import vtkCellLocator # pylint: disable=E0611
from vtkmodules.vtkCommonCore import vtkIdList # pylint: disable=E0611
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid # pylint: disable=E0611

def cell_id_to_indices(cid,grid,irregular=False,key_input=False,tol=0.0001):
    """
    Function to calculate vtk ruc indices from vtk cell id

    Parameters:
        cid (int): input vtk cell id
        grid (vtkRectilinearGrid or vtkUnstructuredGrid): input vtk grid
        irregular (bool): flag to distinguish between macroapi grid inputs
        key_input (bool): flag to distinguish between plot modes
        tol (float): tolerance on line searching


    Returns:
        None.
    """

    if irregular and not key_input:
        ix=grid.GetCellData().GetArray("MarcoAPI Element ID").GetValue(cid)
        iy=0
        iz=0
    elif key_input:
        ix=grid.GetCellData().GetArray("SM-IND").GetValue(cid)
        iy=0
        iz=0
    else:
        if not isinstance(grid, vtkUnstructuredGrid):
            nx, ny, _ = grid.GetDimensions()
            ioff=1 #dimensions are based on points
        else:
            bounds=grid.GetBounds()
            #Create cell locator
            cloc=vtkCellLocator()
            cloc.SetDataSet(grid)
            cloc.BuildLocator()

            pts=[bounds[0]-1,bounds[1]+1,bounds[2]-1, \
                 bounds[3]+1,bounds[4]-1,bounds[5]+1]

            xcells=vtkIdList()
            ycells=vtkIdList()
            zcells=vtkIdList()
            # print('bounds: ', bounds)
            cloc.FindCellsAlongLine([pts[0],bounds[2],bounds[4]],
                                    [pts[1],bounds[2],bounds[4]],tol,xcells)
            # print('xloc: ', [pts[0],bounds[2],bounds[4]],[pts[1],bounds[2],bounds[4]])
            nx=xcells.GetNumberOfIds()
            cloc.FindCellsAlongLine([bounds[0],pts[2],bounds[4]],
                                    [bounds[0],pts[3],bounds[4]],tol,ycells)
            # print('yloc: ', [bounds[0],pts[2],bounds[4]],[bounds[0],pts[3],bounds[4]])
            ny=ycells.GetNumberOfIds()
            cloc.FindCellsAlongLine([bounds[0],bounds[2],pts[4]],
                                    [bounds[0],bounds[2],pts[5]],tol,zcells)
            # print('zloc: ', [bounds[0],bounds[2],pts[4]],[bounds[0],bounds[2],pts[5]])
            # nz=zcells.GetNumberOfIds()
            # print('nx,ny,nz: ', nx,ny,nz)
            ioff=0 #based on cells, not points

        # Calculate the cell indices
        ix = cid % (nx - ioff) #fastest changing dimension
        iy = (cid // (nx - ioff)) % (ny - ioff)
        iz = cid // ((nx - ioff) * (ny - ioff)) #slowest changing dimension

    return ix, iy, iz
