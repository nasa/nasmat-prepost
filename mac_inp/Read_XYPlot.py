"""function to read *XYPLOT keyword""" #pylint: disable=C0103
from .Get_Param_Update_Dict import get_param_update_dict
from .Read_Line import read_line



def Read_XYPlot(f): #pylint: disable=C0103
    """
    function to read *XYPLOT keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        xy (dict): parameters from keyword
    """
    xy={}

    ft=f.tell()
    d,_=read_line(f)
    xy=get_param_update_dict(d,xy,' ','=')

    xy['macro']={}
    xy['micro']={}
    for i in range(2): #pylint: disable=W0612
        mt={}
        ft=f.tell()
        d,_=read_line(f)
        mt=get_param_update_dict(d,mt,' ','=')
        mt['results']={}

        s=''
        n=[]
        if 'macro' in mt:
            n = mt['macro']
            s = 'macro'
        elif 'micro' in mt:
            n = mt['micro']
            s = 'micro'

        for j in range(n):
            ft=f.tell()
            d,_=read_line(f)
            c={}
            c=get_param_update_dict(d,c,' ','=')
            mt['results'][str(j)]=c

        xy[s]=mt

    if d.startswith('*'):
        f.seek(ft)
        return xy

    # print(xy)
    return xy
