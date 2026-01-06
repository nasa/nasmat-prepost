
"""Function to plot a 2D or 3D rectilinear grid, with and without results.""" #pylint: disable=C0103

from .make_grid_2D_3D import make_grid_2d_3d
from .update_h5 import update_h5

from .make_vtk_plot import make_vtk_plot

def vtk_plot_2d_3d(self,dflag='2D'):
    """
    Function to initialize array of default orientations (not used, testing routine)

    Parameters:
        dflag (str): problem dimension

    Returns:
        None
    """
    if not self.update_res_only:
        self.grid = make_grid_2d_3d(self.ruc,self.vs['map'],dflag)

    if self.vs['show_res']:
        update_h5(self.grid,self.h5,self.ruc,self.vs,dflag)

    make_vtk_plot(self,dflag)
