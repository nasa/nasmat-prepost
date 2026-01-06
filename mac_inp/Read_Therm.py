"""function to read *THERM keyword""" #pylint: disable=C0103
from .Get_Param_Update_Dict import get_param_update_dict
from .Read_Line import read_line



def Read_Therm(f): #pylint: disable=C0103
    """
    function to read *THERM keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        t (dict): parameters from keyword
    """

    t={}
    ft=f.tell()
    d,_=read_line(f)

    t=get_param_update_dict(d,t,' ','=')

    if d.startswith('*'):
        f.seek(ft)
        return t

    return t
