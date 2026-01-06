"""class for creating vtk plots of grid objects with and without results shown """
import cv2
from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter,vtkActor,vtkPolyDataMapper # pylint: disable=E0611
from vtkmodules.vtkCommonDataModel import vtkPolyData # pylint: disable=E0611
from vtkmodules.vtkFiltersSources import vtkOutlineSource # pylint: disable=E0611
from vtkmodules.vtkInteractionWidgets import vtkBoxWidget # pylint: disable=E0611
from vtkmodules.vtkFiltersCore import vtkImplicitPolyDataDistance # pylint: disable=E0611
from vtkmodules.vtkFiltersExtraction import vtkExtractGeometry # pylint: disable=E0611
from .vtk_plot_2D_3D import vtk_plot_2d_3d
from .vtk_plot_stacks import vtk_plot_stacks
from .vtk_plot_ugrid import vtk_plot_ugrid
from .vtk_plot_MT import vtk_plot_mt

class VtkPlot():
    """
    VtkPlot - creates vtk plots based for unit cells and finite element meshes
    """
    def __init__(self, opt='2DR', ruc=None, h5=None, hidemat=None, rw=None, vs=None,
                all_rucs=None, grp_mats=None,no_stack=None,sweep=None,update_res_only=False):
        """
        initialize class

        Parameters:
        opt (str): plot option string: '2DR','2DWeave','3DR','MacroAPI'
        ruc (dict): ruc parameters
        h5 (GetH5 class): h5 results
        hidemat (list): ints of material integers to hide in the plot
        rw (vtkRenderWindow): vtk render window
        vs (dict): vtk settings
        all_rucs (dict): all relavant rucs for plotting (used for stacks)
        grp_mats (dict): mapping from mapped sm value to new desired value
        no_stack(list): rucs to not plot as stacks
        sweep(tuple): two start/finish increments for plotting

        Returns:
            None.
        """

        self.opt=opt
        self.ruc=ruc
        self.h5=h5
        self.hidemat=hidemat
        self.rw=rw
        self.vs=vs
        self.all_rucs=all_rucs
        self.grp_mats=grp_mats
        self.no_stack=no_stack
        self.sweep=sweep
        self.vis_subs_mapper=None
        self.box_widget=None
        self.box_actor=None
        self.update_res_only=update_res_only
        self.grid=None
        self.box_widget_init=None

    def _start_render(self):
        """
        Function to start vtk renderer

        Parameters:
            None.

        Returns:
            None.
        """

        if not self.sweep:
            self.vs['make_video']=False
            if 'ind' in self.vs.keys():
                start = self.vs['ind']
            else:
                start = 0
            finish = start + 1
        else:
            start,finish = self.sweep
            self._setup_video()
            self.vs['sweep']=self.sweep
        for ind in range(start,finish):
            self.vs['ind']=ind
            if self.opt=='2DR':
                vtk_plot_2d_3d(self)
            elif self.opt=='3DR':
                vtk_plot_2d_3d(self,dflag='3D')
            elif self.opt=='STACKS':
                vtk_plot_stacks(self)
            elif self.opt=='MT':
                vtk_plot_mt(self)
            elif self.opt=='MacroAPI':
                vtk_plot_ugrid(self, dflag='3D',macroapi=True)
            else:
                print('WARNING: Selected option not available: ',self.opt)

    def start(self):
        """
        Short function name to start vtk renderer

        Parameters:
            None.

        Returns:
            None.
        """

        self._start_render()

    def _setup_video(self):
        """
        function to setup output video

        Parameters:
            None.

        Returns:
            None.
        """

        self.vs['make_video']=True
        self.vs['window_to_image_filter'] = vtkWindowToImageFilter()
        self.vs['window_to_image_filter'].SetInput(self.rw)
        self.vs['window_to_image_filter'].SetInputBufferTypeToRGB()
        self.vs['window_to_image_filter'].ReadFrontBufferOff()
        self.vs['window_to_image_filter'].Update()

        frame_width = self.rw.GetSize()[0]
        frame_height = self.rw.GetSize()[1]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4 files #pylint: disable=E1101
        outname=self.vs['video_outfile']
        out = cv2.VideoWriter(outname, fourcc, self.vs['video_fps'], (frame_width, frame_height))#pylint: disable=E1101

        self.vs['video'] = out

    def set_clipper(self,new_bounds=None):
        """
        function to setup RUC clipper in visualization

        Parameters:
            new_bounds (list): 6 floats defining the bounds

        Returns:
            None.
        """

        grid=self.vis_subs_mapper.GetInput()
        bounds = grid.GetBounds()
        if not new_bounds:
            update_init=False
            # Find center of grid
            center = [(bounds[0] + bounds[1]) / 2,
                      (bounds[2] + bounds[3]) / 2,
                      (bounds[4] + bounds[5]) / 2]
            #Set bounds of clipper to be larger than grid using a scale factor
            sf = 1.1
            new_bounds = [center[0] - (center[0] - bounds[0]) * sf,
                          center[0] + (bounds[1] - center[0]) * sf,
                          center[1] - (center[1] - bounds[2]) * sf,
                          center[1] + (bounds[3] - center[1]) * sf,
                          center[2] - (center[2] - bounds[4]) * sf,
                          center[2] + (bounds[5] - center[2]) * sf]
            self.box_widget_init = new_bounds
        else:
            self.box_widget_init=bounds
            update_init=True

        # Create a mapper and actor for the box (for visualization purposes)
        box_source = vtkOutlineSource()
        box_source.SetBounds(new_bounds)
        box_mapper = vtkPolyDataMapper()
        box_mapper.SetInputConnection(box_source.GetOutputPort())
        box_actor = vtkActor()
        box_actor.SetMapper(box_mapper)
        box_actor.GetProperty().SetColor(1, 0, 0)  #red
        box_actor.VisibilityOff()
        self.rw.GetRenderers().GetFirstRenderer().AddActor(box_actor)

        #Add a vtkBoxWidget for interactivity
        box_widget = vtkBoxWidget()
        box_widget.SetInteractor(self.rw.GetInteractor())
        box_widget.SetProp3D(box_actor)
        box_widget.SetPlaceFactor(1.0)  # Match the box bounds exactly
        box_widget.PlaceWidget(new_bounds)
        # box_widget.SetHandleSize(0.1)
        box_widget.Off()  # Start with the widget disabled

        #Use an implicit distance function to decide what cells are inside a the box widget
        implicit_distance = vtkImplicitPolyDataDistance()

        # Filter to extract cells within the box - excludes boundary cells
        def _update_slicing(widget, event): #pylint: disable=W0613
            """
            function to update RUC slicing in visualization

            Parameters:
                widget (vtkBoxWidget): object to update
                event (str): name of event (not used)
            Returns:
                None.
            """
            polydata = vtkPolyData()
            widget.GetPolyData(polydata)
            implicit_distance.SetInput(polydata)
            self.vs['slicer-bounds']=polydata.GetBounds()
            extract_geometry = vtkExtractGeometry()
            extract_geometry.SetImplicitFunction(implicit_distance)
            extract_geometry.SetInputData(grid)
            extract_geometry.Update()

            self.vis_subs_mapper.SetInputData(extract_geometry.GetOutput())
            self.rw.Render()

        box_widget.AddObserver("InteractionEvent", _update_slicing)
        if update_init:
            _update_slicing(box_widget,None)

        self.vis_subs_mapper.Modified()
        self.box_widget=box_widget
        self.box_actor=box_actor

    def get_clipper(self):
        """
        returns objects from RUC clipper

        Parameters:
            None.

        Returns:
            box_widget (vtkBoxWidget): output widget for clipping
            box_actor (vtkActor): actor for box_widget
            box_widget_init (vtkBoxWidget): initial box widget prior to any clipping
        """
        return self.box_widget,self.box_actor,self.box_widget_init
