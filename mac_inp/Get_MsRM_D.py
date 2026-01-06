""" Function to get RUC D vectors for built-in materials.""" #pylint: disable=C0103
import math
import numpy as np

def get_msrm_d(sm,xang):
    """
    Function to get RUC D vectors for built-in materials

    Parameters:
        sm (int): built-in material number
        xang (float): rotation angle

    Returns:
        d (dict): RUC D vectors
    """

    d={}
    xang=xang*math.pi/180.0 #convert deg to rad
    if -10<=sm<0:
        d['d1']=np.array([1.0,0.0,0.0],dtype=np.double)
        d['d2']=np.array([0.0,1.0,0.0],dtype=np.double)
        d['d3']=np.array([0.0,0.0,1.0],dtype=np.double)
    elif sm==-11:
        d['d1']=np.array([0.0,0.0,1.0],dtype=np.double)
        d['d2']=np.array([1.0,0.0,0.0],dtype=np.double)
        d['d3']=np.cross(d['d1'],d['d2'])
    elif sm==-12:
        d['d1']=np.array([0.0,1.0,0.0],dtype=np.double)
        d['d2']=np.array([1.0,0.0,0.0],dtype=np.double)
        d['d3']=np.cross(d['d1'],d['d2'])

    elif sm==-13:
        d['d1']=np.array([math.tan(xang),1.0,0.0],dtype=np.double)
        d['d2']=np.array([-1.0,math.tan(xang),0.0],dtype=np.double)
        d['d3']=np.cross(d['d1'],d['d2'])

    elif sm==-14:
        d['d1']=np.array([-math.tan(xang),1.0,0.0],dtype=np.double)
        d['d2']=np.array([-1.0,-math.tan(xang),0.0],dtype=np.double)
        d['d3']=np.cross(d['d1'],d['d2'])

    elif sm==-15:
        d['d1']=np.array([math.tan(xang),0.0,1.0],dtype=np.double)
        d['d2']=np.array([-1.0,0.0,math.tan(xang)],dtype=np.double)
        d['d3']=np.cross(d['d1'],d['d2'])

    elif sm==-16:
        d['d1']=np.array([-math.tan(xang),0.0,1.0],dtype=np.double)
        d['d2']=np.array([-1.0,0.0,-math.tan(xang)],dtype=np.double)
        d['d3']=np.cross(d['d1'],d['d2'])


    np.linalg.norm(d['d1'],2)
    np.linalg.norm(d['d2'],2)
    np.linalg.norm(d['d3'],2)

    return d
