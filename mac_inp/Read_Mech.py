"""function to read *MECH keyword""" #pylint: disable=C0103
from .Get_Param_Update_Dict import get_param_update_dict
from .Read_Line import read_line

def Read_Mech(f): #pylint: disable=C0103
    """
    function to read *MECH keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        m (dict): parameters from keyword
    """

    m={}
    ft=f.tell()

    d,m['comments']=read_line(f)

    m=get_param_update_dict(d,m,' ','=')

    nblks=0
    if m['lop']<=6:
        nblks=1
    elif m['lop']>6 and m['lop']<=12:
        nblks=2
    elif m['lop']==99:
        nblks=6

    blk={}
    for i in range(nblks):
        blk[str(i)]={}
        ft=f.tell()
        d,blk[str(i)]['comments']=read_line(f)
        blk[str(i)]=get_param_update_dict(d,blk[str(i)],' ','=')
        mode = blk[str(i)]['mode']
        if not isinstance(mode,list):
            blk[str(i)]['mode']=[mode]
    m['blocks']=blk

    if d.startswith('*'):
        f.seek(ft)
        return m

    return m
