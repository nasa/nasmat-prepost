"""function to read *SOLVER keyword""" #pylint: disable=C0103
from .Get_Param_Update_Dict import get_param_update_dict
from .Read_Line import read_line



def Read_Solver(f): #pylint: disable=C0103
    """
    function to read *SOLVER keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        s (dict): parameters from keyword
    """
    s={'method':1,'opt':0,'itmax':1,'err':0.001,'nleg':0,'ninteg':1}
    ft=f.tell()
    d,_=read_line(f)

    s=get_param_update_dict(d,s,' ','=')
    ft=f.tell()
    d,_=read_line(f)

    if d.startswith('*'):
        f.seek(ft)
        return s

    s=get_param_update_dict(d,s,' ','=')

    if not isinstance(s['stp'],list):
        s['stp']=[s['stp']]

    if isinstance(s['err'],list):
        s['err']=s['err'][0]

    return s
