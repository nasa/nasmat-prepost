"""Generates plot for Mori-Tanaka method.""" # pylint: disable=C0103
import numpy as np

from vtkmodules.vtkCommonCore import vtkIntArray,vtkFloatArray # pylint: disable=E0611
from vtkmodules.vtkCommonDataModel import vtkPolyData,vtkSphere,vtkImplicitBoolean # pylint: disable=E0611
from vtkmodules.vtkFiltersCore import vtkAppendPolyData,vtkClipPolyData # pylint: disable=E0611
from vtkmodules.vtkCommonTransforms import vtkTransform # pylint: disable=E0611
from vtkmodules.vtkFiltersSources import vtkPlaneSource # pylint: disable=E0611
from util.convert_to_2nd_order_tensor import convert_to_2nd_order_tensor
from util.convert_to_voigt import convert_to_voigt
from .make_vtk_plot import make_vtk_plot

def get_fiber_matrix_pd(vf,sm,vmap=None): #pylint: disable=R0915
    """
    Function to create plot for visualizing Mori-Tanaka method results

    Parameters:
        vf (float): input fiber volume fraction
        sm (array): array of indexed material numbers
        vmap (dict): dict to map to actual material numbers

    Returns:
        matrix_pd (vtkPolyData): matrix polydata after clipping
        matrix_pd (vtkPolyData): fiber polydata after clipping
    """

    #Define box
    box = vtkPlaneSource()
    box.SetXResolution(20)
    box.SetYResolution(20)
    box.SetOrigin(0, 0, 0)
    box.SetPoint1(1, 0, 0)
    box.SetPoint2(0, 1, 0)

    #Define sphere at the center of box
    transformsphere = vtkTransform()
    transformsphere.Identity()
    transformsphere.Translate(0.5, 0.5, 0)
    transformsphere.Inverse()
    #vf=A=pi*r^2 assuming a unit cube
    rad=np.sqrt(vf/np.pi)
    sphere = vtkSphere()
    sphere.SetTransform(transformsphere)
    sphere.SetRadius(rad)

    #Clip box with sphere to get cells inside (fiber) and outside (matrix) sphere
    boolean = vtkImplicitBoolean()
    boolean.AddFunction(sphere)
    clipper = vtkClipPolyData()
    clipper.SetInputConnection(box.GetOutputPort())
    clipper.SetClipFunction(boolean)
    clipper.GenerateClippedOutputOn()
    clipper.GenerateClipScalarsOn()
    clipper.SetValue(0)
    clipper.Update()

    matrix_pd=clipper.GetOutput()
    fiber_pd=clipper.GetClippedOutput()

    #assign material number for matrix
    cell_data=vtkIntArray()
    cell_data.SetNumberOfComponents(1)
    cell_data.SetName('SM-IND')
    cell_data.SetNumberOfTuples(matrix_pd.GetNumberOfCells())
    [cell_data.InsertValue(i,sm[0][1][0]) for i in range(matrix_pd.GetNumberOfCells())] #pylint: disable=W0106
    matrix_pd.GetCellData().AddArray(cell_data)

    #assign material number for fiber
    cell_data=vtkIntArray()
    cell_data.SetNumberOfComponents(1)
    cell_data.SetName('SM-IND')
    cell_data.SetNumberOfTuples(fiber_pd.GetNumberOfCells())
    [cell_data.InsertValue(i,sm[0][0][0]) for i in range(fiber_pd.GetNumberOfCells())] #pylint: disable=W0106
    fiber_pd.GetCellData().AddArray(cell_data)

    if vmap:
        sm_act = np.vectorize(vmap.get)(sm)
        cell_data=vtkIntArray()
        [cell_data.InsertValue(i,sm_act[0][1][0]) for i in range(matrix_pd.GetNumberOfCells())] #pylint: disable=W0106
        cell_data.SetName('SM')
        cell_data.SetNumberOfComponents(1)
        cell_data.SetNumberOfTuples(matrix_pd.GetNumberOfCells())
        matrix_pd.GetCellData().AddArray(cell_data)
        [cell_data.InsertValue(i,sm_act[0][0][0]) for i in range(fiber_pd.GetNumberOfCells())] #pylint: disable=W0106
        cell_data.SetName('SM')
        cell_data.SetNumberOfComponents(1)
        cell_data.SetNumberOfTuples(fiber_pd.GetNumberOfCells())
        fiber_pd.GetCellData().AddArray(cell_data)

    return matrix_pd, fiber_pd


def vtk_plot_mt(self):
    """
    Function to create plot for visualizing Mori-Tanaka method results

    Parameters:
        None.

    Returns:
        None.
    """

    ruc=self.ruc
    vs=self.vs
    h5=self.h5


    #get fiber and matrix polydata
    matrix_pd, fiber_pd=get_fiber_matrix_pd(ruc['h'][0], ruc['sm'],vs['map'])

    if vs['show_res']:
        res=vs['selected_result']
        lvl = res['lvl']
        msm=res['matnum']
        ic=res['subvol']
        pid=res['ruc']
        nb=res['parent-NB']
        ng=res['parent-NG']
        #lvl,pid,msm,ia,ib,ig,ipa,ipb,ipg,inc

        if 'h5-parent' in vs.keys():
            grp=vs['h5-parent']
        else:
            grp=None

        h5str=h5.get_data_str(lvl,pid,msm,ic,nb,ng,1,1,1,vs['ind']+1,grp)
        h5grp=h5.get_data_by_str(h5str)


        h5data=h5grp["{vs['var']}"][:,:,:,:,:,:,:]

        #Rotate to material coordinate system if necessary
        if vs['rotate_to_material']:
            allowed_rotations=['Strain','ME.Strain','IN.Strain','TH.Strain','ALPHA','Stress']
            eng_shear=True
            if vs['var'] in allowed_rotations:
                perform_rotation=True
                if vs['var']=='Stress':
                    eng_shear=False
            else:
                perform_rotation=False
                print(f"Rotation not performed for {vs['var']}")

            if perform_rotation and 'ROT' not in h5grp:
                print('WARNING: ROT array not available to rotate to material axes.')
                perform_rotation = False

            if perform_rotation:
                orig_shape=h5data.shape
                data_per_cell = h5data.reshape(-1,h5data.shape[-1])
                rotdata=np.array(h5grp['ROT'][:,:,:,:,:,:,:])
                rot = rotdata.reshape(-1,rotdata.shape[-1]).reshape((-1, 3, 3))
                rott = np.transpose(rot, axes=(0, 2, 1))
                global_tensors=convert_to_2nd_order_tensor(data_per_cell,eng_shear=eng_shear)
                local_tensors = rot @ global_tensors @ rott
                newdata=convert_to_voigt(local_tensors,eng_shear=eng_shear)
                h5data=newdata.reshape(orig_shape)

        h5data=h5data[:,:,:,:,:,:,vs['comp']]
        h5data=np.moveaxis(h5data,0,2)
        #print('var,comp: ', vs['var'],vs['comp'])

        #assigning data for the fiber
        cell_data=vtkFloatArray()
        cell_data.SetNumberOfComponents(1)
        cell_data.SetName(vs['var'])
        cell_data.SetNumberOfTuples(fiber_pd.GetNumberOfCells())
        [cell_data.InsertValue(i,h5data[0,0,0,0,0,0]) for i in range(fiber_pd.GetNumberOfCells())] #pylint: disable=W0106
        fiber_pd.GetCellData().AddArray(cell_data)

        # print(h5data[:,0,0,0,0,0])
        #assigning data for the matrix
        cell_data=vtkFloatArray()
        cell_data.SetNumberOfComponents(1)
        cell_data.SetName(vs['var'])
        cell_data.SetNumberOfTuples(matrix_pd.GetNumberOfCells())
        [cell_data.InsertValue(i,h5data[1,0,0,0,0,0]) for i in range(matrix_pd.GetNumberOfCells())] #pylint: disable=W0106
        matrix_pd.GetCellData().AddArray(cell_data)
        # print('shp: ', h5data.shape)
        # print('data 0: ',h5data[0,0,0,0,0,0])
        # print('data 1: ',h5data[1,0,0,0,0,0])

    #Append polydata
    pdappend = vtkAppendPolyData()
    pdappend.AddInputData(matrix_pd)
    pdappend.AddInputData(fiber_pd)
    pdappend.Update()

    pdall = vtkPolyData()
    pdall.DeepCopy(pdappend.GetOutput())
    self.grid=pdall

    dflag='2D'
    self.vs['show_subvol_edges']=False
    # make_vtk_plot(self,dflag,edges_to_plot=clipper.GetOutput())
    make_vtk_plot(self,dflag)
