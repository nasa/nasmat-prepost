"""function to read *MATLAB keyword""" #pylint: disable=C0103
from .Get_Param_Update_Dict import get_param_update_dict
from .Read_Line import read_line

def Read_Matlab(f): #pylint: disable=C0103
    """
    function to read *MATLAB keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        m (dict): parameters from keyword
    """

    m={'p':0,'v':0,'jskip':1}
    ft=f.tell()
    d,_=read_line(f)

    m=get_param_update_dict(d,m,' ','=')

    if d.startswith('*'):
        f.seek(ft)
        return m

    # print(m)
    return m
