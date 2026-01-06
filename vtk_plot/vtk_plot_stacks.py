"""Function for making plot of RUC stacks."""
import numpy as np
from vtkmodules.vtkFiltersCore import vtkAppendFilter  # pylint: disable=E0611
from vtk.util.numpy_support import numpy_to_vtk # pylint: disable=E0401,E0611
from tqdm import tqdm
from util.cell_id_to_indices import cell_id_to_indices
from .make_grid_2D_3D import make_grid_2d_3d
from .scale_grid import scale_grid
from .make_vtk_plot import make_vtk_plot
#from .update_h5 import update_h5

def vtk_plot_stacks(self):
    """
    Function to generate plot of RUC stacks

    Parameters:
        None.

    Returns:
        None.
    """

    ruc=self.ruc
    vs=self.vs
    h5=self.h5
    all_rucs=self.all_rucs
    grp_mats=self.grp_mats
    if not self.no_stack:
        no_stack=[]
    else:
        no_stack=self.no_stack

    imap={str(vs['map'][key]):int(key) for key in vs['map'].keys()}
    #find maximum dimension for all unit cells contained within ruc - used for scaling
    maxd=0.0
    for key in all_rucs.keys():
        if key=='0':
            continue
        ruci = all_rucs[key]
        if ((ruci['mod'] in (103,203)) and
            np.isin(imap[key],ruc['sm']) and
            int(key) not in no_stack):
            sumd=np.sum(ruci['d'])
            maxd = max(maxd,sumd)

    if 'd' in ruc.keys():
        maxd=max(maxd,np.sum(ruc['d']))

    if maxd==0.0:
        maxd = np.sqrt(np.sum(ruc['h'])+np.sum(ruc['l']))

    maingrid = make_grid_2d_3d(ruc,vs['map'],dflag=ruc['DIM'])
    sm = maingrid.GetCellData().GetArray('SM-IND')
    newgrids=[]

    #gets ic index - not used
    # def get_ic_2d(idx, NG):
    #    i = idx // NG
    #    j = idx % NG
    #    return i * NG + j + 1

    # if 'd' in ruc.keys():
    #     d_off = np.cumsum(np.insert(ruc['d'],0,0))
    h_off = np.cumsum(np.insert(ruc['h'],0,0))
    l_off = np.cumsum(np.insert(ruc['l'],0,0))

    # for i in range(maingrid.GetNumberOfCells()):
    for i in tqdm(range(maingrid.GetNumberOfCells()),desc='Processing stacks for viz: ',
                                                    total=maingrid.GetNumberOfCells()):
        cell=maingrid.GetCell(i)
        mat=int(sm.GetValue(i))

        b=list(cell.GetBounds())
        ix,iy,iz = cell_id_to_indices(i, maingrid)

        if ruc['DIM']=='2D':
            offsets=[0.0,iy*vs['offset'][1]+h_off[iy], ix*vs['offset'][0]+l_off[ix]]
            extents=[b[1]-b[0],b[3]-b[2],maxd]
            l_ext,h_ext,d_ext=extents

        elif ruc['DIM']=='3D':
            offsets=[0.0,iy*vs['offset'][1]+h_off[iy], iz*vs['offset'][0]+l_off[iz]]
            extents=[maxd,b[3]-b[2],b[5]-b[4]]
            d_ext,h_ext,l_ext=extents
        else:
            d_ext,h_ext,l_ext=1.0,1.0,1.0

        mat_act=vs['map'][mat] #changed default behavior

        if mat_act < 0 and mat_act not in no_stack: #ruc
            cellgrid = make_grid_2d_3d(all_rucs[str(mat_act)],vs['map'],dflag=None)
        else: #constituent
            tmpruc={'na':1,'nb':1,'ng':1,'mod':103,
                    'd':np.array(d_ext),
                    'h':np.array(h_ext),
                    'l':np.array(l_ext),
                    'sm':mat*np.ones([1,1,1]),
                    'ORI_X1': np.zeros([1,3]),
                    'ORI_X2': np.zeros([1,3]),
                    'ORI_X3': np.zeros([1,3]),
                    'ORI_X1_NORM': np.zeros([1]),
                    'ORI_X2_NORM': np.zeros([1]),
                    'ORI_X3_NORM': np.zeros([1])}
            cellgrid = make_grid_2d_3d(tmpruc,vs['map'],dflag=None)

        cellgrid = scale_grid(cellgrid,extents)
        pts=cellgrid.GetPoints()

        for j in range(cellgrid.GetNumberOfPoints()):
            pt = pts.GetPoint(j)
            new_pt = tuple(pt[k]+offsets[k] for k in range(3))
            pts.SetPoint(j, new_pt)

        if vs['show_res']:
            # TODO: Implement update_h5 call for stacks
            #cellruc=all_rucs[str(mat_act)]
            # update_h5(cellgrid,h5,cellruc,vs,cellruc['DIM'])
            #Ex: 'Level 1 2D RUC - M=0,SubVol.:1,RUCID:0'
            get_by_ind=False
            if mat_act < 0 and mat_act not in no_stack:
                nb=ruc['nb']
                ng=ruc['ng']
                get_by_ind=True
                ic=-1
                pid=-1
                ind=[iz+1,iy+1,ix+1]
                pid=-1
                msm=mat_act
                lvl=vs['selected_result']['lvl']+1
            else:
                nb=vs['selected_result']['parent-NB']
                ng=vs['selected_result']['parent-NG']
                ic=vs['selected_result']['subvol']
                pid=vs['selected_result']['ruc']
                msm=vs['selected_result']['matnum']
                lvl=vs['selected_result']['lvl']
                ind=None

            if vs['h5-parent']:
                grp=vs['h5-parent']
            else:
                grp=None

            h5str=h5.get_data_str(lvl,pid,msm,ic,nb,ng,1,1,1,vs['ind']+1,grp,ind)
            h5grp=h5.get_data_by_str(h5str)

            if get_by_ind:
                h5data=h5grp[f"{vs['var']}"][:,:,:,:,:,:,vs['comp']]
            else:
                h5data=h5grp[f"{vs['var']}"][iz,ix,iy,:,:,:,vs['comp']]

            h5a = numpy_to_vtk(h5data.flatten())
            h5a.SetNumberOfComponents(1)
            h5a.SetName(vs['var'])
            cellgrid.GetCellData().AddArray(h5a)

        newgrids.append(cellgrid)

    appendfilter = vtkAppendFilter()
    for grid in newgrids:
        appendfilter.AddInputData(grid)
    appendfilter.Update()

    combined = appendfilter.GetOutput()

    if grp_mats:
        sm=combined.GetCellData().GetArray('SM')
        for i in range(sm.GetNumberOfValues()):
            if int(sm.GetValue(i)) in grp_mats.keys():
                sm.SetValue(i,grp_mats[int(sm.GetValue(i))])

    self.grid=combined
    make_vtk_plot(self,dflag='3D')
