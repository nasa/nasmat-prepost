"""function to read *HDF5 keyword""" #pylint: disable=C0103
from .Get_Param_Update_Dict import get_param_update_dict
from .Read_Line import read_line

def Read_HDF5(f): #pylint: disable=C0103
    """
    function to read *HDF5 keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        h (dict): parameters from keyword
    """

    h={'popt1':0,'popt2':0,'maxlev':0}
    ft=f.tell()
    d,_=read_line(f)

    if d.startswith('*'):
        f.seek(ft)
        return h

    h=get_param_update_dict(d,h,' ','=')
    return h
