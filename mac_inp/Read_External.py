"""function to read *EXTERNAL_SETTINGS keyword""" #pylint: disable=C0103
from .Get_Param_Update_Dict import get_param_update_dict
from .Read_Line import read_line



def Read_External(f): #pylint: disable=C0103
    """
    function to read *EXTERNAL_SETTINGS keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        e (dict): parameters from keyword
    """

    e={}

    for i in range(2): #pylint: disable=W0612
        ft=f.tell()
        d,_=read_line(f)
        e=get_param_update_dict(d,e,' ','=')

    if d.startswith('*'):
        f.seek(ft)
        return e

    # print(e)
    return e
