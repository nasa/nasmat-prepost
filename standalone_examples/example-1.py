"""Example 1: Reading an existing MAC file, Running, and Plotting Results""" #pylint: disable=C0103

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
from mac_inp import mac_inp #pylint: disable=C0413
from NASMAT import NASMAT #pylint: disable=C0413
from geth5 import GetH5 #pylint: disable=C0413
from vtk_plot import VtkPlot #pylint: disable=C0413

#Define NASMAT input deck filename and location
INFILE='HF2D_w_failure.MAC'
INFILE=os.path.join(os.getcwd(),'standalone_examples',INFILE)
#Define options
RUN_NASMAT = True #Sets up and runs NASMAT - assumes job executes successfully
PLOT = 'RUC' #Select variable to plot: RUC, MAX-STRESS, MAX-DMG
SCREEN_SZ_FACTORS = (0.3,0.5) #width and height factors for setting the render window size [0-1]

##################################################################################################
# Get existing NASMAT environment. See README for details on setting variables
npps = get_npp_settings(echo=True)

# Read in the mac input file - easier for pointing to data later
mi = mac_inp(name=INFILE)

# Run NASMAT if desired
if RUN_NASMAT:
    nasmat=NASMAT(npps['NASMAT_SOLVER'],npps['HDF5_PATH'],npps['INTEL_PATH'],npps['INTEL_OPTS'])
    nasmat.run(mac=INFILE)

#Get output data if plotting results:
base, _ = os.path.splitext(INFILE)
h5file = base+'.h5'
if PLOT!='RUC' and os.path.exists(h5file):
    h5=GetH5(h5name=h5file)
    #Find increment with max stress-22
    nincs = h5.get_number_incs()
    stress22 = np.zeros(nincs)
    for i in range(nincs):
        H5STR = (f"NASMAT Data/Level=0/Parent RUCID=0, RUCDef MSM=0, IA=0, IB=0, IG=0, "
                f"IPA=0, IPB=0, IPG=0/Inc={i+1}/Stress")
        h5d = h5.get_data_by_str(H5STR)
        stress22[i] = h5d[..., 1] #extract 22-component of stress
    max_ind = stress22.argmax()
    print(f"Max Stress-22 of {stress22.max()} found at increment {max_ind+1}")
else:
    PLOT='RUC'
    print('WARNING: H5 file not found! Plotting RUC instead.')

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
vs['show_axes'] = False

#Create plot of quantity of interest
VP = None
ruc=mi.mac['ruc']['rucs']['0']
if PLOT=='RUC': #Makes a plot of the RUC showing the materials
    VP=VtkPlot(opt='2DR',ruc=ruc, h5=None, hidemat=[],rw=render_window, vs=vs)
    VP.start()
    save_screenshot(name=base+"-mats.png",rw=render_window)

elif PLOT=='MAX-STRESS':
    vs['show_res']=True
    vs['var']='Stress' #variable to plot
    vs['comp']=1 #0-based index of components
    vs['ind']=max_ind #0-based index to plot
    vs['plot_range'] = [0.0,60.0]
    vs['plot_levels']=7

    #get selected RUC results to plot
    vs['selected_result']=mi.mac['hierarchy']['res']['items']['1']

    VP=VtkPlot(opt='2DR',ruc=ruc, h5=h5, hidemat=[],
                                 rw=render_window, vs=vs)
    VP.start()
    save_screenshot(name=base+f"-S22-INC{max_ind+1}.png",rw=render_window)

elif PLOT=='MAX-DMG':
    #Note: the DMG array value selected is calculated by:
    #      D = 1 - S22_0/S22
    #          where D is the scalar damage variable
    #                S22_0 is the initial 22-component of the compliance matrix
    #                S22 is the current 22-component of the compliance matrix
    vs['show_res']=True
    vs['var']='DMG' #variable to plot
    vs['comp']=1 #0-based index of components
    vs['ind']=nincs-1 #0-based index to plot
    vs['plot_range'] = [0.0,1.0]
    vs['plot_levels']=5

    #get selected RUC results to plot
    vs['selected_result']=mi.mac['hierarchy']['res']['items']['1']

    VP=VtkPlot(opt='2DR',ruc=ruc, h5=h5, hidemat=[],
                                 rw=render_window, vs=vs)
    VP.start()
    save_screenshot(name=base+f"-D22-INC{nincs}.png",rw=render_window)

interactor.Start()
