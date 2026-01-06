"""Gets arrows for displaying coordinate systems."""
from vtkmodules.vtkFiltersSources import vtkArrowSource # pylint: disable=E0611
from vtkmodules.vtkCommonColor import vtkNamedColors # pylint: disable=E0611
from vtkmodules.vtkCommonMath import vtkMatrix4x4 # pylint: disable=E0611
from vtkmodules.vtkCommonTransforms import vtkTransform # pylint: disable=E0611
from vtkmodules.vtkRenderingCore import vtkActor,vtkPolyDataMapper,vtkFollower # pylint: disable=E0611
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter # pylint: disable=E0611
from vtkmodules.vtkRenderingFreeType import vtkVectorText # pylint: disable=E0611


def add_arrow_label(text, pos, scale):
    """
    Function to get and scale an arrow text label

    Parameters:
        text (str): label text to display
        pos (list): 3 floats to define position of label
        scale (float): scale factor to adjust label size

    Returns:
        label_actor (vtkFollower): arrow label
    """

    label = vtkVectorText()
    label.SetText(text)

    label_mapper = vtkPolyDataMapper()
    label_mapper.SetInputConnection(label.GetOutputPort())

    label_actor = vtkFollower()
    label_actor.SetMapper(label_mapper)
    label_actor.SetScale(scale,scale,scale)
    label_actor.SetPosition(pos)

    colors = vtkNamedColors()
    label_actor.GetProperty().SetColor(colors.GetColor3d("Black"))

    return label_actor

def get_arrow(arrow_length, sf, color_name,
              rotate_axis=None, rotate_angle=0.0):
    """
    Function to create and transform a vtkActor arrow

    Parameters:
        arrow_length (float): base arrow length
        sf (float): scale factor
        color_name (str): name of arrow color (e.g., "Red", "Green", "Blue")
        rotate_axis (str, optional): axis of rotation ("X", "Y", or "Z")
        rotate_angle (float): rotation angle in degrees

    Returns:
        gactor (vtkActor): vtkActor object representing the arrow
    """

    colors = vtkNamedColors()

    # Apply the transforms for coordinate system
    matrix = vtkMatrix4x4()
    matrix.Identity()

    transform = vtkTransform()
    transform.Translate([0.0, 0.0, 0.0])
    transform.Concatenate(matrix)
    transform.Scale(arrow_length * sf, arrow_length * sf, arrow_length * sf)

    # Apply rotation
    if rotate_axis == "X":
        transform.RotateX(rotate_angle)
    elif rotate_axis == "Y":
        transform.RotateY(rotate_angle)
    elif rotate_axis == "Z":
        transform.RotateZ(rotate_angle)

    arrowsource = vtkArrowSource()
    arrowsource.SetTipResolution(31)
    arrowsource.SetShaftResolution(21)
    arrowsource.SetTipLength(0.3)
    arrowsource.SetTipRadius(0.03)
    arrowsource.SetShaftRadius(0.01)

    transformpd = vtkTransformPolyDataFilter()
    transformpd.SetTransform(transform)
    transformpd.SetInputConnection(arrowsource.GetOutputPort())

    arrowmapper = vtkPolyDataMapper()
    arrowmapper.SetInputConnection(transformpd.GetOutputPort())

    gactor = vtkActor()
    gactor.SetMapper(arrowmapper)
    gactor.GetProperty().SetColor(colors.GetColor3d(color_name))

    return gactor


def get_coord_sys(grid,dflag,vs):
    """
    Function to get and scale an arrow text label

    Parameters:
        grid (vtkRectilinearGrid or vtkUnstructuredGrid): vtk grid object
        dflag (str): problem dimension
        vs (dict): vtk settings

    Returns:
        arrow_actors (list): vtkActor objects representing coordinate system arrows
        label_actors (list): vtkFollower objects respresenting labels
    """

    # Set up visualization graphics
    arrow_actors = []
    b = list(grid.GetBounds())

    length = 1.0
    if dflag=='2D':
        length = min(b[1]-b[0], b[3]-b[2])
    elif dflag=='3D':
        length=min(b[1]-b[0],b[3]-b[2],b[5]-b[4])
    #length=2



    if 'arrow_scale_factor' in vs.keys():
        sf=vs['arrow_scale_factor']
    else:
        sf=1.5

    # Apply the transforms for coordinate system -- 1-direction
    if dflag=='3D':
        arrow_actors.append(get_arrow(length, sf,"Red"))

    # Apply the transforms for coordinate system -- 2-direction
    arrow_actors.append(get_arrow(length, sf,"Green",'Z',90.0))

    # Apply the transforms for coordinate system -- 3-direction
    if dflag=='3D':
        arrow_actors.append(get_arrow(length, sf,"Blue",'Y',-90.0))
    else:
        arrow_actors.append(get_arrow(length, sf,"Blue"))

    # TODO: fix label display
    # posL=length*1.5
    # posOff=-length*0.08
    # sf=0.01
    # label_x1 = add_arrow_label("X1", [posL, posOff, posOff],0.2*sf)
    # label_x2 = add_arrow_label("X2", [posOff, posL, posOff],0.2*sf)
    # label_x3 = add_arrow_label("X3", [posOff, posOff, posL],0.2*sf)
    # label_actors=[label_x1,label_x2,label_x3]
    label_actors=[]

    return arrow_actors, label_actors
