"""functions to support plotting and manipulating 2D weaves in UI""" #pylint: disable=C0103
import numpy as np
import vtkmodules.vtkRenderingOpenGL2# pylint: disable=W0611
from vtkmodules.vtkRenderingCore import (# pylint: disable=E0611
    vtkActor,vtkCamera,vtkDataSetMapper,
    vtkCellPicker,vtkSelectVisiblePoints,vtkActor2D)
from vtkmodules.vtkRenderingLabel import vtkLabeledDataMapper# pylint: disable=E0611

from vtkmodules.vtkCommonCore import (# pylint: disable=E0611
    vtkIntArray,vtkLookupTable,vtkIdTypeArray)

from vtkmodules.vtkCommonDataModel import (# pylint: disable=E0611
    vtkRectilinearGrid,vtkUnstructuredGrid,
    vtkSelection,vtkSelectionNode)
from vtkmodules.vtkFiltersCore import vtkIdFilter,vtkCellCenters # pylint: disable=E0611
from vtkmodules.vtkFiltersExtraction import vtkExtractSelection # pylint: disable=E0611
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage # pylint: disable=E0611

from vtk.util.numpy_support import vtk_to_numpy #pylint: disable=E0401,E0611
from vtk.util.numpy_support import numpy_to_vtk #pylint: disable=E0401,E0611


class MouseInteractorStyle(vtkInteractorStyleImage): #pylint: disable=C0103,R0903
    """defines mouse interaction behavior for 2d weave UI"""
    def __init__(self, vis,grid,ruc):
        """
        initialize class

        Parameters:
            vis (vtkUnstructuredGrid): input grid for only visible cells
            grid (vtkRectilinearGrid): original, full input grid
            ruc (dict): ruc parameters
        
        Returns:
            None.
        """

        self.AddObserver('LeftButtonPressEvent', self.leftbuttonpressevent)
        self.vis=vis
        self.grid=grid
        self.ruc=ruc

    def leftbuttonpressevent(self,_,__): #pylint: disable=R0914
        """
        function that reverses weave pattern and updates data by left-clicking

        Parameters:
            None.
        
        Returns:
            None.
        """

        #Get click location
        pos = self.GetInteractor().GetEventPosition()
        #Get cell at click location
        picker = vtkCellPicker()
        picker.SetTolerance(0.0005)
        picker.Pick(pos[0], pos[1], 0, self.GetDefaultRenderer())
        #Update if cell found
        if picker.GetCellId() != -1:
            #Extract selected cell from self.vis
            ids = vtkIdTypeArray()
            ids.SetNumberOfComponents(1)
            ids.InsertNextValue(picker.GetCellId())
            selection_node = vtkSelectionNode()
            selection_node.SetFieldType(vtkSelectionNode.CELL)
            selection_node.SetContentType(vtkSelectionNode.INDICES)
            selection_node.SetSelectionList(ids)
            selection = vtkSelection()
            selection.AddNode(selection_node)
            extract_selection = vtkExtractSelection()
            extract_selection.SetInputData(0, self.vis)
            extract_selection.SetInputData(1, selection)
            extract_selection.Update()
            selected = vtkUnstructuredGrid()
            selected.ShallowCopy(extract_selection.GetOutput())
            #Update material numbers if only one cell selected
            if selected.GetNumberOfCells()==1:
                #Get material number and original id of cell
                #    for both self.vis and self.grid
                ocd=selected.GetCellData()
                pk=int(ocd.GetArray('PICKABLE').GetComponent(0,0))
                smso=ocd.GetArray('SM').GetComponent(0,0)
                oid=int(ocd.GetArray('ID').GetComponent(0,0))
                oidv=int(ocd.GetArray('ID_VIS').GetComponent(0,0))
                #Get material numbers for self.vis and self.grid
                vis_sm=self.vis.GetCellData().GetArray('SM')
                orig_sm=self.grid.GetCellData().GetArray('SM')
                #Flip matids only if cell is pickable
                # print('old SM: ', self.ruc['sm'][1,:])
                # print('picked SM: ', smso)
                if pk:
                    if int(smso)==1: #change from 1 to 2
                        orig_sm.SetComponent(oid,0,2)
                        vis_sm.SetComponent(oidv,0,2)
                    elif int(smso)==2: #change from 2 to 1
                        orig_sm.SetComponent(oid,0,1)
                        vis_sm.SetComponent(oidv,0,1)
                    #Update render window
                    orig_sm.Modified()
                    vis_sm.Modified()
                    sm=vtk_to_numpy(orig_sm)
                    self.ruc['sm']=sm.reshape((self.ruc['nb'],self.ruc['ng']))
                    # print('new SM: ', self.ruc['sm'][1,:])

                    renwini=self.GetInteractor()
                    renwin=renwini.GetRenderWindow()
                    renwin.Render()

        self.OnLeftButtonDown()
#*****************************************************************************
class Gen_VTK_Plot_2DWeave(): #pylint: disable=R0903
    """
    Gen_VTK_Plot_2DWeave - Creates selectable plot of 2D weave
    """
    def __init__(self,ruc,rw,show_mats=False):
        """
        initialize class

        Parameters:
            ruc (dict): ruc data for 2D weave
            rw (vtkRenderWindow): VTK render window object
            show_mats (bool): flag to show material ids for debugging
        
        Returns:
            None.
        """

        self.ruc=ruc
        self.rw=rw
        self.show_mats=show_mats
        self.grid = None
        self.vis_subs = None

        #create the 2d weave grid
        self._make_ruc()
        #plot ruc
        self._plot()

    def _make_ruc(self):
        """
        makes grid for RUC and assigns arrays

        Parameters:
            None.
        
        Returns:
            None.
        """

        ruc=self.ruc
        d = np.array([0.0,0.001]) #second value cannot be zero!
        h = np.cumsum(np.insert(ruc['h'],0,0))
        l = np.cumsum(np.insert(ruc['l'],0,0))
        grid = vtkRectilinearGrid()
        grid.SetDimensions(ruc['ng']+1, ruc['nb']+1,2)
        grid.SetXCoordinates(numpy_to_vtk(l))
        grid.SetYCoordinates(numpy_to_vtk(h))
        grid.SetZCoordinates(numpy_to_vtk(d))

        self.grid=grid

        self._set_int1_array('SM',ruc['sm'].astype(int).ravel())
        self._set_int1_array('ID',np.arange(grid.GetNumberOfCells()))
        self._set_int1_array('PICKABLE',ruc['pickable'].astype(int).ravel())


    def _set_int1_array(self,name,inparray):
        """
        creates 1d vtkIntArray and adds to grid

        Parameters:
            name (str): name of the vtk array
            inparray (np.ndarray): 1d array to be converted added to grid
        
        Returns:
            None.
        """

        ilen = self.grid.GetNumberOfCells()
        iarray=vtkIntArray()
        iarray.SetNumberOfComponents(1)
        iarray.SetName(name)
        iarray.SetNumberOfTuples(ilen)
        [iarray.InsertValue(i,inparray[i]) for i in range(ilen)] #pylint: disable=W0106

        cell_data = self.grid.GetCellData()
        cell_data.AddArray(iarray)

    def _plot(self):
        """
        creates plot for RUC

        Parameters:
            None.
        
        Returns:
            None.
        """

        rw=self.rw
        grid=self.grid
        ruc=self.ruc

        renderer=rw.GetRenderers().GetFirstRenderer()
        renderer.RemoveAllViewProps()
        renderer.ResetCamera()

        camera =vtkCamera()
        camera.SetPosition(0, 0, 100)
        camera.SetFocalPoint(0, 0, 0)

        renderer.SetBackground(1.0,1.0,1.0)
        rw.AddRenderer(renderer)
        renderer.SetActiveCamera(camera)

        self._get_vis_subs()
        # print('vis_subs.GetNumberOfCells(): ', self.vis_subs.GetNumberOfCells())


        mapper = vtkDataSetMapper()
        mapper.SetInputData(self.vis_subs)

        lut = vtkLookupTable()
        lut.Build()
        mapper.SetLookupTable(lut)
        mapper.SetScalarRange(self.vis_subs.GetCellData().GetArray('SM').GetRange())

        actor=vtkActor()
        actor.GetProperty().SetEdgeVisibility(False)
        actor.GetProperty().SetLineWidth(0.5)
        actor.SetMapper(mapper)
        actor.GetProperty().SetOpacity(1.0)

        if self.show_mats:
            self._show_mats()

        # Get renderer and interactor from window
        rwi = rw.GetInteractor()
        rwi.SetInteractorStyle(vtkInteractorStyleImage())
        style = MouseInteractorStyle(self.vis_subs,grid,ruc)
        style.SetDefaultRenderer(renderer)
        rwi.SetInteractorStyle(style)

        renderer.AddActor(actor)
        renderer.ResetCamera()
        renderer.ResetCameraClippingRange()

        rw.Modified()
        rw.Render()

    def _get_vis_subs(self):
        """
        function to get visible cells for selection

        Parameters:
            None.
        
        Returns:
            None.
        """

        ids = vtkIdTypeArray()
        ids.SetNumberOfComponents(1)
        visids = vtkIntArray()
        visids.SetNumberOfComponents(1)
        visids.SetName('ID_VIS')
        alist=self.grid.GetCellData().GetArray('SM')
        idv=0
        for i in range(alist.GetNumberOfValues()):
            if int(alist.GetComponent(i,0))==3:
                ids.InsertNextValue(i)
            else:
                visids.InsertNextValue(idv)
                idv+=1
        selectionnode = vtkSelectionNode()
        selectionnode.SetFieldType(vtkSelectionNode.CELL)
        selectionnode.SetContentType(vtkSelectionNode.INDICES)
        selectionnode.SetSelectionList(ids)
        selection = vtkSelection()
        selection.AddNode(selectionnode)
        extractselection = vtkExtractSelection()
        extractselection.SetInputData(0, self.grid)
        extractselection.SetInputData(1, selection)
        extractselection.Update()
        selected = vtkUnstructuredGrid()
        selected.ShallowCopy(extractselection.GetOutput())
        # print('cell type = ', selected.GetCellType(0))
        #print("There are %s cells in the selection" % selected.GetNumberOfCells())
        hideactor = vtkActor()
        hideactor.GetProperty().SetOpacity(0)
        hidemapper = vtkDataSetMapper()
        hidemapper.SetInputData(selected)
        selectionnode.GetProperties().Set(vtkSelectionNode.INVERSE(), 1)
        extractselection.Update()
        vis_subs = vtkUnstructuredGrid()
        vis_subs.ShallowCopy(extractselection.GetOutput())
        vis_subs.GetCellData().AddArray(visids)
        vis_subs.GetCellData().SetActiveScalars('SM')

        self.vis_subs = vis_subs

    def _show_mats(self):
        """
        function to show material ids on plot

        Parameters:
            None.
        
        Returns:
            None.
        """
        renderer=self.rw.GetRenderers().GetFirstRenderer()
        array_names = {self.vis_subs.GetCellData().GetArrayName(i):i
                        for i in range(self.vis_subs.GetCellData().GetNumberOfArrays())}

        ids = vtkIdFilter()
        ids.SetInputData(self.vis_subs)
        ids.CellIdsOff()
        ids.SetFieldData(1)
        ids.PointIdsOff()
        ids.FieldDataOn()
        ids.Update()
        cc = vtkCellCenters()
        cc.SetInputConnection(ids.GetOutputPort())
        viscells = vtkSelectVisiblePoints()
        viscells.SetInputConnection(cc.GetOutputPort())
        viscells.SetRenderer(renderer)
        cellmapper = vtkLabeledDataMapper()
        cellmapper.SetInputConnection(viscells.GetOutputPort())
        cellmapper.SetLabelModeToLabelFieldData()
        cellmapper.SetLabelFormat('%d')
        cellmapper.SetFieldDataArray(array_names['SM'])
        cellmapper.SetLabeledComponent(0)
        cellmapper.GetLabelTextProperty().SetColor(0, 0, 0)
        celllabels = vtkActor2D()
        celllabels.SetMapper(cellmapper)
        renderer.AddActor2D(celllabels)
