"""function to read *PRINT keyword""" #pylint: disable=C0103
from .Get_Param_Update_Dict import get_param_update_dict
from .Read_Line import read_line

def Read_Print(f): #pylint: disable=C0103
    """
    function to read *PRINT keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        p (dict): parameters from keyword
    """

    p={'npl':1,'vflev':0}
    ft=f.tell()
    d,_=read_line(f)

    if d.startswith('*'):
        f.seek(ft)
        return p

    p=get_param_update_dict(d,p,' ','=')

    return p
