"""function to read *FAILURE_SUBCELL keyword""" #pylint: disable=C0103
from .Get_Param_Update_Dict import get_param_update_dict
from .Read_Line import read_line



def Read_FailureSubcell(f): #pylint: disable=C0103
    """
    function to read *FAILURE_SUBCELL keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        fs (dict): parameters from keyword
    """

    fs={}

    ft=f.tell()
    d,_=read_line(f)
    fs=get_param_update_dict(d,fs,' ','=')

    fs['mats']={}
    for i in range(fs['nmat']): #pylint: disable=W0612,R1702
        mt={}
        ft=f.tell()
        d,mt['comments']=read_line(f)
        mt=get_param_update_dict(d,mt,' ','=')
        mt['crits']={}
        for j in range(mt['ncrit']):
            ft=f.tell()
            d,_=read_line(f)
            c={}
            c=get_param_update_dict(d,c,' ','=')
            if 'compr' not in c:
                c['compr']='off'
            # if 'norm' not in c:
            #     c['norm']=1

            if 'ntemp' in c:
                keys = ['temp', 'x11', 'x22', 'x33', 'x23', 'x13', 'x12', 'x11c', 'x22c', 'x33c']
                c.update({k: [] for k in keys})
                for _ in range(c['ntemp']):
                    ft=f.tell()
                    d,_=read_line(f)
                    cc = {}
                    cc=get_param_update_dict(d,cc,' ','=')
                    for k in keys:
                        if k in cc:
                            c[k].append(cc[k])
                for k in list(c):
                    if isinstance(c[k], list) and not c[k]:
                        c.pop(k)

            mt['crits'][str(j)]=c
        fs['mats'][str(mt['mat'])]=mt
    if d.startswith('*'):
        f.seek(ft)
        return fs

    # print(fs)
    return fs
