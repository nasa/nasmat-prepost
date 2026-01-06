"""File to define default vtk settings used for plotting"""

def get_default_vtk_settings():
    """
    function to get default vtk settings for plotting

    Parameters:
        None.

    Returns:
        vtk_settings (dict): default vtk settings
    """

    vtk_settings = {}

    #Map to convert actual material number to 0-based sequential number
    #    Currently found from reading input file
    vtk_settings['map']={}

    #Unit cell defaults
    vtk_settings['show_res']=False #default to not show results
    vtk_settings['hover']=True #hover mode enabled, allows switching to lower level results
    vtk_settings['opacity']=1.0 #controls opacity of unit cell
    vtk_settings['show_ori']=[False,False,False] #show orientation vector if appropriate
    vtk_settings['ori_scale']=None #scale factor for adjusting orienation arrow lengths
    vtk_settings['offset']=[0.1,0.1,0.1] #default offsets in each direction for plotting stacks

    vtk_settings['show_ids']=False #shows actual cell id numbers on subvolumes
                                   #if True (may significnatly slow down visualization!)
    vtk_settings['show_mats']=False #shows material number on subvolumes
                                   #if True (may significnatly slow down visualization!)
    vtk_settings['show_values']=False #shows result values on subvolumes
                                   #if True (may significnatly slow down visualization!)
    vtk_settings['show_subvol_edges']=True #shows subvolume edges in the plot

    vtk_settings['show_title'] = True #shows title text if True
    vtk_settings['show_axes'] = True #shows coordinate axes if True
    vtk_settings['arrow_scale_factor']=1.5 #scale arrow length for coordinate axes

    #NASMAT H5 results file defaults
    vtk_settings['h5-parent']=None #standalone
    vtk_settings['selected_result']={} #initializing result
    vtk_settings['var']='Stress' #HDF5 variable
    vtk_settings['ind']=0 #increment number (0-based)
    vtk_settings['elem']=-1 #default for standalone
    vtk_settings['ip']=-1 #default for standalone
    vtk_settings['scale_res'] = {} #dict for scaling results (limited functionality)
    vtk_settings['plot_levels']=13 #number of scale bar values
    vtk_settings['plot_colorbar_levels']=48 #number of color bar values
    vtk_settings['plot_range']=[] #scale bar range (list of two values, min/max)
    vtk_settings['hide_var_title']=True #hides scalebar title if True
    vtk_settings['cmap']=0 #colormap default -- see make_vtk_plot.py
    vtk_settings['selected-subvol']={'cell_id':None,'indices':[]} #selected subvolume indices
    vtk_settings['rotate_to_material']=False #Flag to rotate unit cell results to material
                                             #coordinate system from unit cell system
    #Camera settings
    vtk_settings['echo-camera-pos']=False #enable to print camera settings to screen
                                          #useful for manually picking/settings views
    vtk_settings['camera-position']=[1,-1,-1] #3 floats to set camera position for 3D plots
    vtk_settings['camera-focal-point']=[0,0,0] #3 floats to set camera focal point for 3D plots
    vtk_settings['camera-view-up']=[1,0,0] #3 floats to set camera view up for 3D plots
    vtk_settings['rotate_grid']=True #allows vtk grid to rotate (True for 3D, False for 2D)

    #Slicer setting
    vtk_settings['slicer-bounds']=None

    #Text settings
    vtk_settings['window_text']=''

    return vtk_settings
