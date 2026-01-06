"""function to read *PDFA keyword""" #pylint: disable=C0103
from .Get_Param_Update_Dict import get_param_update_dict
from .Read_Line import read_line

def Read_PDFA(f): #pylint: disable=C0103
    """
    function to read *PDFA keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        p (dict): parameters from keyword
    """

    p={}

    ft=f.tell()
    d,_=read_line(f)
    p=get_param_update_dict(d,p,' ','=')

    p['mats']={}
    for i in range(p['nmat']): #pylint: disable=W0612
        mt={}
        ft=f.tell()
        d,_=read_line(f)
        mt=get_param_update_dict(d,mt,' ','=')
        ft=f.tell()
        d,_=read_line(f)
        if d.startswith('*'):
            f.seek(ft)
            return p
        mt=get_param_update_dict(d,mt,' ','=')

        p['mats'][str(mt['mat'])]=mt

    if d.startswith('*'):
        f.seek(ft)
        return p

    # print(p)
    return p
