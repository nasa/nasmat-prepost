"""function to read *CONSTITUENTS keyword""" #pylint: disable=C0103
import numpy as np
from .Read_Line import read_line


from .Get_Param_Update_Dict import get_param_update_dict

def Read_Constit(f): #pylint: disable=C0103
    """
    function to read *CONSTITUENTS keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        c (dict): parameters from keyword
    """

    c={}

    d,_=read_line(f)
    c=get_param_update_dict(d,c,' ','=')

    c['mats']={}
    for i in range(c['nmats']):
        m = c['mats'][str(i+1)]={}
        d,m['comments']=read_line(f)
        m=get_param_update_dict(d,m,' ','=')

        if 'D' in m:
            d1=np.asarray(m['D'],dtype=np.double)
            d2=np.zeros([3],dtype=np.double)
            d3=np.zeros([3],dtype=np.double)

            d2[1:]=d1[1:]
            d2[0]=-1*(d1[1]*d1[1]+d1[2]*d1[2])/d1[0]

            d3[0]=0.0
            d3[1]=-1*(d1[0]*d1[2]-d2[1]*d1[2])
            d3[2]=d1[0]*d1[1]-d2[1]*d1[1]

            np.linalg.norm(d1,2)
            np.linalg.norm(d2,2)
            np.linalg.norm(d3,2)
            m['d1']=d1
            m['d2']=d2
            m['d3']=d3

        ft=f.tell()
        d,_=read_line(f)
        while d and not d[0].startswith('*') and not d[0].upper().startswith('M'):
            m=get_param_update_dict(d,m,' ','=')
            ft=f.tell()
            d,_=read_line(f)
        f.seek(ft)

    # print(c)
    return c
