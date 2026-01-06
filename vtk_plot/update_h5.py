"""Updates input grid h5 results."""
import numpy as np
from vtk.util.numpy_support import numpy_to_vtk  # pylint: disable=E0401,E0611
from util.convert_to_2nd_order_tensor import convert_to_2nd_order_tensor
from util.convert_to_voigt import convert_to_voigt

def update_h5(grid,h5,ruc,vs,dflag):
    """
    Function to get and scale an arrow text label

    Parameters:
        grid (vtkRectilinearGrid or vtkUnstructuredGrid): input grid
        h5 (GetH5 class): class containing h5 data
        ruc (dict): ruc parameters
        vs (dict) : vtk settings
        dflag (str): problem definition

    Returns:
        None.
    """

    cell_data=grid.GetCellData()
    array_names=[cell_data.GetArrayName(i) for i in range(cell_data.GetNumberOfArrays())]

    res=vs['selected_result']
    lvl = res['lvl']
    msm=res['matnum']
    ic=res['subvol']
    pid=res['ruc']
    nb=res['parent-NB']
    ng=res['parent-NG']
    #lvl,pid,msm,ia,ib,ig,ipa,ipb,ipg,inc
    if vs['h5-parent']:
        grp=vs['h5-parent']
    else:
        grp=None
    h5str=h5.get_data_str(lvl,pid,msm,ic,nb,ng,1,1,1,vs['ind']+1,grp)
    print('Plotting data at H5 location: ', h5str)
    h5grp=h5.get_data_by_str(h5str)
    h5data=h5grp[f"{vs['var']}"][:,:,:,:,:,:,:]

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

    if dflag=='2D':
        nx,ny,nz = 1,ruc['nb'],ruc['ng']
        idx=np.arange(nx * ny * nz).reshape(nz, ny, nx).transpose(1, 0, 2).flatten()
        h5data = h5data.reshape([nx*ny*nz,h5data.shape[-1]])
        h5data = h5data[idx,:]
        if vs['comp']>h5data.shape[-1]-1:
            h5data=np.linalg.norm(h5data,axis=-1)
        else:
            h5data = h5data[:,vs['comp']]
    elif dflag=='3D':
        if vs['comp']>h5data.shape[-1]-1:
            h5data=np.linalg.norm(h5data,axis=-1)
        else:
            h5data=h5data[:,:,:,:,:,:,vs['comp']]

    if vs['var']=='MATNUM':
        # vs['plot_levels']=12
        # vs['plot_levels']=np.unique(h5data.flatten()).shape[0]
        # vs['plot_levels']=len(vs['map'].keys())
        rev = {v: k for k, v in vs['map'].items()}
        h5data = np.vectorize(rev.get)(h5data)
    # else:
    #     vs['plot_levels']=13

    if vs['scale_res']:
        h5data=h5data/vs['scale_res']['val']
        if 'func' in vs['scale_res'].keys():
            func=vs['scale_res']['func']
            if func=='abs':
                h5data=np.abs(h5data)

    if vs['var'] not in array_names:
        h5d = numpy_to_vtk(h5data.flatten())
        h5d.SetNumberOfComponents(1)
        h5d.SetName(vs['var'])
        cell_data.AddArray(h5d)
    else:
        h5d=cell_data.GetArray(vs['var'])
        h5f=h5data.flatten()
        h5d.SetVoidArray(h5f,len(h5f),1)
        h5d.Modified()
