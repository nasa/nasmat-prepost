"""Function for creating vtk plot of grid """
import cv2
import vtkmodules.vtkRenderingOpenGL2# pylint: disable=W0611
from vtkmodules.vtkRenderingAnnotation import vtkScalarBarActor # pylint: disable=E0611
from vtkmodules.vtkRenderingCore import ( # pylint: disable=E0611
    vtkActor,vtkCamera,vtkDataSetMapper,
    vtkPolyDataMapper,vtkCellPicker,
    vtkSelectVisiblePoints,vtkActor2D)
from vtkmodules.vtkRenderingLabel import vtkLabeledDataMapper # pylint: disable=E0611

from vtkmodules.vtkCommonCore import vtkLookupTable,vtkIdTypeArray,vtkIdList,vtkPoints # pylint: disable=E0611
from vtkmodules.vtkInteractionWidgets import vtkScalarBarWidget # pylint: disable=E0611
from vtkmodules.vtkFiltersCore import (vtkFeatureEdges,vtkIdFilter,vtkGlyph3D,# pylint: disable=E0611
                                    vtkCellCenters,vtkThreshold)
from vtkmodules.vtkCommonColor import vtkColorSeries,vtkNamedColors # pylint: disable=E0611
from vtkmodules.vtkCommonDataModel import ( # pylint: disable=E0611
    vtkUnstructuredGrid,vtkSelection,vtkSelectionNode,vtkDataSetAttributes,
    vtkDataObject,vtkPolyData,vtkCellArray,vtkLine)
from vtkmodules.vtkFiltersExtraction import vtkExtractSelection # pylint: disable=E0611
from vtkmodules.vtkFiltersSources import vtkArrowSource # pylint: disable=E0611
from vtkmodules.vtkRenderingCore import vtkTextActor # pylint: disable=E0611
from vtk.util.numpy_support import vtk_to_numpy # pylint: disable=E0401,E0611
from .get_coord_sys import get_coord_sys

def make_vtk_plot(self,dflag,edges_to_plot=None,macroapi=False):
    """
    Function to create vtk plot

    Parameters:
        dflag (str): problem dimension
        edges_to_plot (vtkPolyData): optional edges to show in plot
        macroapi (str):  flag to indicate data source for plotting

    Returns:
        None.
    """

    rw=self.rw
    grid=self.grid
    vs=self.vs
    hidemat=self.hidemat

    # Get renderer and interactor from window
    rwi = rw.GetInteractor()
    renderer=rw.GetRenderers().GetFirstRenderer()
    renderer.RemoveAllViewProps()

    ids = vtkIdTypeArray()
    ids.SetNumberOfComponents(1)
    if hidemat:
        alist=grid.GetCellData().GetArray('SM-IND')
        [ids.InsertNextValue(i) for i in range(alist.GetNumberOfValues())#pylint: disable=W0106
            for j in hidemat if alist.GetComponent(i,0)==j]

    selectionnode = vtkSelectionNode()
    selectionnode.SetFieldType(vtkSelectionNode.CELL)
    selectionnode.SetContentType(vtkSelectionNode.INDICES)
    selectionnode.SetSelectionList(ids)
    selection = vtkSelection()
    selection.AddNode(selectionnode)
    extractselection = vtkExtractSelection()
    extractselection.SetInputData(0, grid)
    extractselection.SetInputData(1, selection)
    extractselection.Update()
    selected = vtkUnstructuredGrid()
    selected.ShallowCopy(extractselection.GetOutput())
    #print("There are %s cells in the selection" % selected.GetNumberOfCells())
    hideactor = vtkActor()
    hideactor.GetProperty().SetOpacity(0)
    hidemapper = vtkDataSetMapper()
    hidemapper.SetInputData(selected)
    selectionnode.GetProperties().Set(vtkSelectionNode.INVERSE(), 1)
    extractselection.Update()
    vis_subs = vtkUnstructuredGrid()
    vis_subs.ShallowCopy(extractselection.GetOutput())

    # Setup mapper and actors
    mapper2 = vtkDataSetMapper()
    mapper2.SetInputData(vis_subs)
    mapper2.SetScalarModeToUseCellData() #req'd for unstructured grid
                                         #default is to use point data (not defined)
    if (not vs['show_res'] and vis_subs.GetCellData()):
        vis_subs.GetCellData().SetActiveScalars('SM-IND')
        #want to be the full array to keep colors the same
        smrange=grid.GetCellData().GetArray('SM-IND').GetRange()
        # print('SM range: ', smrange)
        if vs['plot_range']:
            mapper2.SetScalarRange(vs['plot_range'])
        else:
            mapper2.SetScalarRange(smrange)

    else:
        vis_subs.GetCellData().SetActiveScalars(vs['var'])
        lut = vtkLookupTable()

        cmap_opt=vs['cmap']-1
        if cmap_opt==-1: #old way
            lut.SetHueRange(0.667, 0.0)
            # lut.SetNumberOfTableValues(256)
            lut.SetNumberOfTableValues(vs['plot_colorbar_levels'])
            lut.Build()
        else: #default colormaps
            colorseries = vtkColorSeries()
            colorseries.SetColorScheme(cmap_opt)
            colorseries.BuildLookupTable(lut,vtkColorSeries.ORDINAL)

        #testing - for outputing colormap points - do not remove!
        # import csv
        # pts=[]
        # for i in range(lut.GetNumberOfTableValues()):
        #     c=lut.GetTableValue(i)
        #     pts.append(list(c[:3]))
        # with open("cmap-pts%d.csv"%(cmap_opt+1), "w", newline="") as csvfile:
        #     writer = csv.writer(csvfile)
        #     writer.writerow(["R", "G", "B"])
        #     writer.writerows(pts)

        srange = vis_subs.GetCellData().GetArray(vs['var']).GetRange()
        print('Actual Data Range in Plot: ', srange)
        if vs['plot_range']:
            mapper2.SetScalarRange(vs['plot_range'])
        else:
            dr=list(srange)
            #this is a temp fix, particularly for MT results
            # if abs(dr[0]-dr[1])<1e-10 and vs['selected_result']['dim']=='MT':
            #     dr[1]+=10
            mapper2.SetScalarRange(dr)
        mapper2.SetLookupTable(lut)

        if vs['var']!='MATNUM':

            scalar_bar = vtkScalarBarActor()
            scalar_bar.SetOrientationToHorizontal()
            scalar_bar.GetLabelTextProperty().SetColor(0, 0, 0)

            if vs['var']=='MATNUM':
                # lutm = vtkLookupTable()
                # lutm.SetNumberOfTableValues(len(vs['map']))
                # lutm.Build()
                # for seq, act in vs['map'].items():
                #     lutm.SetTableValue(seq, seq / len(vs['map']), 0.5, 0.5, 1.0)
                #     lutm.SetAnnotation(seq, str(act))
                # scalar_bar.SetLookupTable(lutm)
                scalar_bar.SetLookupTable(lut)
            else:
                scalar_bar.SetLookupTable(lut)

            scalar_bar.SetNumberOfLabels(vs['plot_levels'])

            if 'scalar_bar_pos' in vs.keys():
                scalar_bar.SetPosition(vs['scalar_bar_pos'])

            vs['title']=vs['var']
            if not vs['hide_var_title']:
                scalar_bar.SetTitle(vs['var'])
                scalar_bar.GetTitleTextProperty().SetColor(0, 0, 0)
            scalar_bar_widget = vtkScalarBarWidget()
            scalar_bar_widget.SetInteractor(rwi)
            scalar_bar_widget.SetCurrentRenderer(renderer)
            scalar_bar_widget.SetScalarBarActor(scalar_bar)

            # position.SetValue(0.1, 0.1)  # X and Y positions
            scalar_bar_widget.On()
            scalar_bar_widget.Render()

            def sb_update(obj,event): #pylint: disable=W0613
                scalar_bar_widget.On()
                scalar_bar_widget.Render()

            rwi.AddObserver('LeftButtonPressEvent',sb_update)

    mapper2.Update()
    self.vis_subs_mapper = mapper2

    cellpicker = vtkCellPicker()
    cellpicker.SetTolerance(0.001)
    rwi.SetPicker(cellpicker)

    # Add actor for highlighted cell edges
    edge_actor = vtkActor()
    edge_mapper = vtkPolyDataMapper()
    edge_actor.SetMapper(edge_mapper)
    edge_actor.GetProperty().SetColor(1, 0, 1) #edge color
    edge_actor.GetProperty().SetLineWidth(5) #size of edges
    renderer.AddActor(edge_actor)

    #callback for mouse movement
    def mouse_move(obj, event): #pylint: disable=W0613
        mouse_pos = rwi.GetEventPosition()
        cellpicker.Pick(mouse_pos[0], mouse_pos[1], 0, renderer)
        cell_id = cellpicker.GetCellId()
        if cell_id != -1:
            # Get the picked cell
            dataset = cellpicker.GetDataSet()

            #account for case where edges are hovered over (vtkPolyData objects)
            if not isinstance(dataset, vtkUnstructuredGrid):
                edge_actor.VisibilityOff()
                rw.Render()
                return

            point_ids = vtkIdList()
            dataset.GetCellPoints(cell_id, point_ids)

            # Create a new vtkPoints object for the cell
            cell_points = vtkPoints()
            for i in range(point_ids.GetNumberOfIds()):
                cell_points.InsertNextPoint(dataset.GetPoint(point_ids.GetId(i)))

            # Create edges for the picked cell
            edge_poly_data = vtkPolyData()
            edges = vtkCellArray()

            if not macroapi:
                # Define the edges of a voxel (3D rectangular cell)
                edge_connections = [
                (0, 1), (1, 3), (3, 2), (2, 0),  # Bottom face
                (4, 5), (5, 7), (7, 6), (6, 4),  # Top face
                (0, 4), (1, 5), (2, 6), (3, 7)]   # Vertical edges
            else:
                #Define edges of an unstructured element from macroapi
                edge_connections = [
                (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom face
                (4, 5), (5, 6), (6, 7), (7, 4),  # Top
                (0, 4), (1, 5), (2, 6), (3, 7)]   # Vertical edges


            for edge in edge_connections:
                line = vtkLine()
                line.GetPointIds().SetId(0, edge[0])
                line.GetPointIds().SetId(1, edge[1])
                edges.InsertNextCell(line)

            edge_poly_data.SetPoints(cell_points)
            edge_poly_data.SetLines(edges)

            edge_poly_data.SetPoints(cell_points)
            edge_poly_data.SetLines(edges)

            edge_mapper.SetInputData(edge_poly_data)
            edge_actor.VisibilityOn()
        else:
            edge_actor.VisibilityOff()

        rw.Render()

    # Add observers for hover behavior
    if vs['hover']:
        if 'tag_MouseMove' in vs.keys():
            rwi.RemoveObserver(vs['tag_MouseMove'])
        vs['tag_MouseMove']=rwi.AddObserver("MouseMoveEvent", mouse_move)


    actor2 = vtkActor()

    if 'show_subvol_edges' not in vs.keys():
        vs['show_subvol_edges']=True
    if not edges_to_plot and not vs['show_subvol_edges']:
        actor2.GetProperty().SetEdgeVisibility(False)
    else:
        actor2.GetProperty().SetEdgeVisibility(True)
    actor2.SetMapper(mapper2)
    actor2.GetProperty().SetOpacity(vs['opacity'])
    renderer.AddActor(actor2)
    #renderer.AddActor(hideActor) #uncomment to show hidden cells

    arrow_actors,label_actors=get_coord_sys(grid,dflag,vs)
    if vs['show_axes']:
        [renderer.AddActor(i) for i in arrow_actors]#pylint: disable=W0106
        [renderer.AddActor(i) for i in label_actors]#pylint: disable=W0106

    if any(vs['show_ori']):
        colors = vtkNamedColors()
        c=['Red','Green','Blue']
        for i in range(3):
            var=f"ORI_X{i+1}"
            if not vs['show_ori'][i]:
                continue

            vis_subs.GetCellData().SetActiveScalars(var+'_NORM')
            vis_subs.GetCellData().SetActiveVectors(var)

            nz=vtkThreshold()
            nz.SetInputArrayToProcess(0, 0, 0,
                            vtkDataObject.FIELD_ASSOCIATION_CELLS,
                            vtkDataSetAttributes.SCALARS)
            nz.SetInputData(vis_subs)
            nz.SetLowerThreshold(1e-5)
            #nz.SetAttributeModeToUseCellData()
            nz.Update()

            cell_centers = vtkCellCenters()
            # cell_centers.SetInputData(vis_subs)
            cell_centers.SetInputData(nz.GetOutput())
            arrow = vtkArrowSource()
            arrow_glyph = vtkGlyph3D()
            arrow_glyph.SetSourceConnection(arrow.GetOutputPort())
            arrow_glyph.SetInputConnection(cell_centers.GetOutputPort())
            arrow_glyph.SetVectorModeToUseVector()
            if not vs['ori_scale']:
                vs['ori_scale']=1.0
            arrow_glyph.SetScaleFactor(vs['ori_scale'])
            arrow_mapper = vtkPolyDataMapper()
            arrow_mapper.SetInputConnection(arrow_glyph.GetOutputPort())
            arrow_mapper.ScalarVisibilityOff()
            arrow_actor = vtkActor()
            arrow_actor.SetMapper(arrow_mapper)
            arrow_actor.GetProperty().SetColor(colors.GetColor3d(c[i]))
            renderer.AddActor(arrow_actor)
        vis_subs.GetCellData().SetActiveScalars('SM-IND')

    if edges_to_plot:
        boundary = vtkFeatureEdges()
        boundary.SetInputData(edges_to_plot)
        boundary.BoundaryEdgesOn()  # Only extract boundary edges
        boundary.FeatureEdgesOff()
        boundary.ManifoldEdgesOff()
        boundary.NonManifoldEdgesOff()
        boundary.ColoringOff()
        boundary.Update()


        emapper = vtkPolyDataMapper()
        emapper.SetInputData(boundary.GetOutput())
        emapper.SetScalarRange([0,1])
        emapper.SetScalarVisibility(1)
        emapper.SetScalarModeToUsePointData()
        emapper.GetLookupTable().SetTableRange([0,1])
        emapper.GetLookupTable().SetHueRange(0, 0)
        emapper.GetLookupTable().SetValueRange(0, 0)

        eactor = vtkActor()
        eactor.SetMapper(emapper)
        eactor.GetProperty().SetEdgeVisibility(1)
        eactor.GetProperty().SetLineWidth(3.0)
        eactor.GetProperty().SetColor(0, 0, 0)

        renderer.AddActor(eactor)


    array_names = {vis_subs.GetCellData().GetArrayName(i):i
                    for i in range(vis_subs.GetCellData().GetNumberOfArrays())}
    ids = vtkIdFilter()
    ids.SetInputData(vis_subs)

    self.grid.DeepCopy(vis_subs)

    if vs['show_mats'] or vs['show_values']:
        ids.CellIdsOff()
        ids.SetFieldData(1)
    elif vs['show_ids']:
        ids.CellIdsOn()

    if vs['show_mats'] or vs['show_ids'] or vs['show_values']:
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
        if vs['show_values']:
            cellmapper.SetLabelFormat('%f')
            array_id=array_names[vs['var']]
            cellmapper.SetFieldDataArray(array_id)
        elif vs['show_ids']:
            cellmapper.SetLabelFormat('%d')
            array_id=array_names['vtkOriginalCellIds']
        else:
            cellmapper.SetLabelFormat('%d')
            array_id=array_names['SM']
            cellmapper.SetFieldDataArray(array_id)

        cellmapper.SetLabeledComponent(0)
        cellmapper.GetLabelTextProperty().SetColor(0, 0, 0)
        celllabels = vtkActor2D()
        celllabels.SetMapper(cellmapper)
        renderer.AddActor2D(celllabels)

    camera =vtkCamera()
    if vs['camera-focal-point'] and dflag=='3D':
        camera.SetFocalPoint(vs['camera-focal-point'])
    else:
        camera.SetFocalPoint(0, 0, 0)

    if vs['camera-position'] and dflag=='3D':
        camera.SetPosition(vs['camera-position'])
    else:
        camera.SetPosition(0, 0, 100)

    if vs['camera-view-up'] and dflag=='3D':
        camera.SetViewUp(vs['camera-view-up'])
    else:
        camera.SetViewUp(0, 1, 0)

    if vs['echo-camera-pos']:
        def echo_camera_position(caller, event): #pylint: disable=W0613
            pos = camera.GetPosition()
            fp = camera.GetFocalPoint()
            vu = camera.GetViewUp()
            print("Camera Position: ",pos)
            print("Focal Point: ",fp)
            print("View Up: ",vu)

        camera.AddObserver("ModifiedEvent", echo_camera_position)

    renderer.SetActiveCamera(camera)
    renderer.ResetCamera()
    renderer.ResetCameraClippingRange()

    if vs['show_axes']:
        [i.SetCamera(camera) for i in label_actors]#pylint: disable=W0106

    rw.Render()

    text_actor=vtkTextActor()
    text_actor.SetInput(vs['window_text'])
    tp = text_actor.GetTextProperty()
    tp.SetColor(1.0, 0.0, 0.0)
    tp.SetFontSize(24)
    tp.SetVerticalJustificationToTop()
    tp.SetJustificationToLeft()
    pos = text_actor.GetPositionCoordinate()
    pos.SetCoordinateSystemToNormalizedViewport()
    text_actor.SetPosition(0.01, 0.99)

    if vs['show_title']:
        renderer.AddActor(text_actor)

    #create copy of default camera since calls above modify default settings
    if 'default_camera' not in vs:
        vs['default_camera']=vtkCamera()
        vs['default_camera'].DeepCopy(camera)

    rw.Render()

    if vs['make_video']:

        vs['window_to_image_filter'].Modified()
        vs['window_to_image_filter'].Update()

        vtk_image = vs['window_to_image_filter'].GetOutput()
        width, height, _ = vtk_image.GetDimensions()

        vtk_array = vtk_image.GetPointData().GetScalars()
        components = vtk_array.GetNumberOfComponents()
        arr = vtk_to_numpy(vtk_array)
        arr = arr.reshape(height, width, components)
        frame = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)# pylint: disable=E1101
        frame = cv2.flip(frame, 0)# pylint: disable=E1101

        vs['video'].write(frame)
        if vs['ind']==vs['sweep'][1]-1:
            vs['video'].release()
