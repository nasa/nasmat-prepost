"""Example 2: Importing a grid (VTU file) of a plain weave RUC into NASMAT.
              Creates a multiscale model manually, plots various quanities.
              Optional logic to convert weave to stacks
""" #pylint: disable=C0103

import os
import sys
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vtkmodules.vtkRenderingCore import (# pylint: disable=E0611,W0404,C0413
    vtkRenderWindow,vtkRenderWindowInteractor,
    vtkRenderer,vtkRenderWindowInteractor,vtkWindowToImageFilter)
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera # pylint: disable=E0611,C0413
from vtkmodules.vtkIOImage import vtkPNGWriter # pylint: disable=E0611,C0413

from util.npp_settings import get_npp_settings #pylint: disable=C0413
from util.get_default_vtk_settings import get_default_vtk_settings #pylint: disable=C0413
from util.stackify import Stackify #pylint: disable=C0413
from file_importer import FileImporter #pylint: disable=C0413
from nasmat_defaults import nasmat_defaults #pylint: disable=C0413
from mac_out import mac_out #pylint: disable=C0413
from mac_inp import mac_inp #pylint: disable=C0413
from NASMAT import NASMAT #pylint: disable=C0413
from geth5 import GetH5 #pylint: disable=C0413
from vtk_plot import VtkPlot #pylint: disable=C0413

#Define NASMAT input deck filename and location
INFILE='PW_20_20_10.vtu'
INFILE=os.path.join(os.getcwd(),'standalone_examples',INFILE)
#Define options
RUN_NASMAT = True #Sets up and runs NASMAT - assumes job executes successfully
CONVERT_TO_STACKS = False #converts the weave RUC to stacks
PLOT = 'RUC' #Select variable to plot: RUC, RUC-ORI, STRESS
SCREEN_SZ_FACTORS = (0.3,0.5) #width and height factors for setting the render window size [0-1]

##################################################################################################
#A simple vtkUnstructuredGrid for a plain weave was created using TexGen.
#Map TexGen array mateiral names and orientations to required inputs
array_mapping={'mat':'YarnIndex','ori':'Orientation'}
#Read in the model
model=FileImporter(filename=INFILE,array_mapping=array_mapping)
#Convert the model to NASMAT format
model.perform_conversion()

#Create NASMAT dict for outputting model
nasmatkw={}
#Get NASMAT defaults (also can be defined manually)
ndef=nasmat_defaults()

#-Add *CONSTITUENTS
nasmatkw['constit']={'nmats':5,'mats':{}}
avail_mats=ndef.mats
c={'1':avail_mats['IM7'].copy(),'2':avail_mats['IM7'].copy(),
    '3':avail_mats['IM7'].copy(),'4':avail_mats['IM7'].copy(),
    '5':avail_mats['8552 Epoxy']}
for i in range(1,6): #redefine material number
    c[str(i)]['m']=i
nasmatkw['constit']['mats'].update(c)

#-Add *RUC
#--import starting model
nasmatkw['ruc']=model.ruc
#--create lower level unit cell template for tow - 2x2, vf=0.6
tow_ruc={'msm':0,'mod':102,'archid':99,'nb':2,'ng':2,'DIM':'2D'}
tow_ruc['h']=np.array([0.7745967,0.2254033],dtype=float)
tow_ruc['l']=np.array([0.7745967,0.2254033],dtype=float)
sm_tow=np.ones((2,2))*2
sm_tow[0,0]=1
tow_ruc['sm']=sm_tow
#--add lower level ruc for tows
update_mats={}
mats=model.get_mats()[1:] #get all tows, excludes first number (matrix)
for i,mat in enumerate(mats):
    new_mat=-17-i #new multiscale material number
    update_mats[mat]=new_mat #generate entry for updating original ruc material number
    new_ruc=tow_ruc.copy()
    new_ruc['msm']=new_mat #update msm entry within template
    nasmatkw['ruc']['nrucs']+=1 #update nrucs counter
    nasmatkw['ruc']['rucs'].update({str(new_mat):new_ruc}) #add tow ruc to list of others

#--update SM in highest unit cell
update_mats[-1]=5 #TexGen sets -1 to be the matrix material, update that to be a positive number
print('material mapping (old to new):',update_mats)
mapper=np.vectorize(lambda x: update_mats.get(x, x))
nasmatkw['ruc']['rucs']['0']['sm'] = mapper(nasmatkw['ruc']['rucs']['0']['sm'])
nasmatkw['ruc']['rucs']['0']['mod']=203 #HFGMC3D for weave

#-Add in *MECH, 2% strain loading in 2-direction
nasmatkw['mech']={'lop':2,'blocks':{
                    '0':{'npt':2,'ti':[0.0,1.0],'mag':[0.0,0.02],'mode':[1]}
                    }}

#-Add in *SOLVER (single step since no failure included)
nasmatkw['solver']={'method':1,'npt':2,'ti':[0.0,1.0],
                    'stp':[1.0],'itmax':100,'err':1e-5}

#-Add in *PROBLEM_TYPE
nasmatkw['probtype']={'mech':1,'vect':0} #perform only mechanical analysis

#-Add in *XYPLOT
results={}
results['0']={'name':'PW-strain-stress-22','x':2,'y':8}
nasmatkw['xyplot']={'macro':{'nmacro':len(results.keys()),'results':results}}

#-Add in *HDF5
nasmatkw['hdf5']={'maxlev':3} #output results at all levels

#-Add in *PRINT
nasmatkw['print']={'npl':1} #add incremental output

#Convert model to stack format if desired
base, _ = os.path.splitext(INFILE)
if CONVERT_TO_STACKS:
    macfile=base+'-stacks.MAC'
    s=Stackify(rucs=nasmatkw['ruc']['rucs'],lev0_mod=202,stack_mod=103,
                nmats=nasmatkw['constit']['nmats'],rem_dup=False,
                crot=nasmatkw['ruc']['crot']['0'])
    nasmatkw['ruc']['rucs'].update(s.newrucs)
    nasmatkw['ruc']['nrucs']=len(nasmatkw['ruc']['rucs'].keys())
    nasmatkw['ruc']['crot']=s.newcrot
else:
    macfile=base+'.MAC'

#Create NASMAT input file
mac_out(nasmatkw,macfile)


# Get existing NASMAT environment. See README for details on setting variables
npps = get_npp_settings(echo=True)

# Run NASMAT if desired
if RUN_NASMAT:
    nasmat=NASMAT(npps['NASMAT_SOLVER'],npps['HDF5_PATH'],npps['INTEL_PATH'],npps['INTEL_OPTS'])
    nasmat.run(mac=macfile)

#Get output data if plotting results:
h5file = macfile[:-4]+'.h5'
NINCS=1
if not PLOT.startswith('RUC') and os.path.exists(h5file):
    h5=GetH5(h5name=h5file)
    NINCS = h5.get_number_incs()
elif not PLOT.startswith('RUC') and not os.path.exists(h5file):
    PLOT='RUC'
    print('WARNING: H5 file not found! Plotting RUC instead.')

# Read in the mac input file - easier for pointing to data later
mi = mac_inp(name=macfile)

#VTK setup for plotting
render_window=vtkRenderWindow()
renderer = vtkRenderer()
renderer.SetBackground(*npps['BACKGROUND_COLOR'])
render_window.AddRenderer(renderer)
interactor = vtkRenderWindowInteractor()
interactor.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
render_window.SetInteractor(interactor)
interactor.Initialize()
screen_width, screen_height = render_window.GetScreenSize()
render_window.SetSize(int(SCREEN_SZ_FACTORS[0]*screen_width),
                        int(SCREEN_SZ_FACTORS[1]*screen_height))

#Define helper function for saving screenshots
def save_screenshot(name,rw):
    """
    Helper function save a screenshot

    Parameters:
        name (str): file name with extension
        rw (vtkRenderWindow): render window for plot

    Returns:
        None.
    """

    img_filter = vtkWindowToImageFilter()
    img_filter.SetInput(rw)
    img_filter.Update()
    img_writer = vtkPNGWriter()
    img_writer.SetFileName(name)
    img_writer.SetInputConnection(img_filter.GetOutputPort())
    img_writer.Write()

#Define VTK settings
vs=get_default_vtk_settings()
vs['hover']=False

#Create plot of quantity of interest
VP = None

if CONVERT_TO_STACKS:
    OPT='STACKS'
    mats=[str(mi.mac['mat_map'][key]) for key in mi.mac['mat_map'] if mi.mac['mat_map'][key]<=0]
    all_rucs = {key: mi.mac['ruc']['rucs'][key] for key in mats}
    vs['map'] = mi.mac['mat_map']
else:
    OPT='3DR'
    all_rucs={}

VP = None
ruc=mi.mac['ruc']['rucs']['0']
if PLOT=='RUC': #Makes a plot of the RUC showing the materials
    vs['plot_range'] = [0.0,5.0]
    VP=VtkPlot(opt=OPT,ruc=ruc,h5=None,hidemat=[],rw=render_window,
                vs=vs,all_rucs=all_rucs)
    VP.start()
    save_screenshot(name=macfile[:-4]+"-mats.png",rw=render_window)
elif PLOT=='RUC-ORI': #Makes a plot of the RUC showing the materials
    vs['plot_range'] = [0.0,5.0]
    vs['show_ori']=[True, False, False] #show only 1-direction arrows
    vs['opacity']=0.3 #adjust opacity to see through the RUC
    vs['ori_scale']=0.07 #scale orientation vector length
    hide_matrix=[int(key) for key in mi.mac['mat_map'].keys() if mi.mac['mat_map'][key]==5]
    VP=VtkPlot(opt=OPT,ruc=ruc,h5=None,hidemat=hide_matrix,
                rw=render_window,vs=vs,all_rucs=all_rucs)
    VP.start()
    save_screenshot(name=macfile[:-4]+"-tow-ori.png",rw=render_window)
elif PLOT=='STRESS':
    vs['show_res']=True
    vs['var']='Stress' #variable to plot
    vs['comp']=1 #0-based index of components
    vs['ind']=NINCS-1 #0-based index to plot
    vs['plot_range'] = [0.0,6000.0]
    vs['plot_levels']=7

    #get selected RUC results to plot
    vs['selected_result']=mi.mac['hierarchy']['res']['items']['1']

    VP=VtkPlot(opt=OPT,ruc=ruc,h5=h5,hidemat=[],
                rw=render_window,vs=vs,all_rucs=all_rucs)
    VP.start()
    save_screenshot(name=macfile[:-4]+"-S22.png",rw=render_window)

interactor.Start()
