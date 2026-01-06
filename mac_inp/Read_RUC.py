"""functions to read *RUC keyword""" #pylint: disable=C0103
import math
import os
import numpy as np
from PyQt5.QtWidgets import QMessageBox  # pylint: disable=E0611
from .Get_After_EqSign import get_after_eqsign
from .Get_Param_Update_Dict import get_param_update_dict
from .Read_Line import read_line

def get_builtin_ruc_3d(archid,vf,f,m,r,asp,p): #pylint: disable=R0912,R0913,R0914,R0915,R0917
    """
    function to set up built-in NASMAT 3D RUCs

    Parameters:
        archid (int): NASMAT *RUC ARCHID parameter for RUC
        vf (int): NASMAT *RUC VF parameter for RUC
        f (int): NASMAT *RUC F parameter for RUC
        m (int): NASMAT *RUC M parameter for RUC
        r (int): NASMAT *RUC R parameter for RUC
        asp (int): NASMAT *RUC ASP parameter for RUC
        p (int): NASMAT *RUC P parameter for RUC

    Returns:
        ruc (dict): ruc parameters
    """

    if archid==0:

        na=1
        nb=1
        ng=1

        sm=np.zeros([ng,nb,na],dtype=np.int32)
        xd=np.zeros(na,dtype=np.double)
        xh=np.zeros(nb,dtype=np.double)
        xl=np.zeros(ng,dtype=np.double)

        xd[0]=1.0
        xh[0]=1.0
        xl[0]=1.0
        sm[0,0,0]=m

    elif archid==1:
        na = 2
        nb = 2
        ng = 2

        sm=np.zeros([ng,nb,na],dtype=np.int32)
        xd=np.zeros(na,dtype=np.double)
        xh=np.zeros(nb,dtype=np.double)
        xl=np.zeros(ng,dtype=np.double)

        for ia in range(1,na+1):
            for ib in range(1,nb+1):
                for ig in range(1,ng+1):
                    iss = ia + (ib - 1) * na + (ig - 1) * na * nb

                    if iss==1:
                        sm[ig-1,ib-1,ia-1] = f
                    else:
                        sm[ig-1,ib-1,ia-1] = m

        sol=np.roots([1,0,-vf * (asp - 1) / asp, - vf / asp])
        sol = [root.real for root in sol if np.isclose(root.imag, 0)]

        xh[0] = sol[0]
        xd[0] = asp *xh[0]
        xl[0] = xh[0]
        xh[1] = 1 - xh[0]
        xl[1] = 1 - xl[0]
        xd[1] = xh[1]


    elif archid==13:
        #hard-wired for now...
        na=2
        sumd=1

        if 'NMSUB' not in p.keys():
            p['NMSUB']=1

        nmsub=p['NMSUB']

        if r >= 1:
            if vf > 0.80613 / r:
                vf = 0.80613 / r
                print('**** WARNING ****')
                print(f"MAX VF EXCEEDED, USING MAX VALUE OF {vf}")
                print('**** WARNING ****')
        else:
            if vf > 0.80613 * r:
                vf = 0.80613 * r
                print('**** WARNING ****')
                print(f"MAX VF EXCEEDED, USING MAX VALUE OF {vf}")
                print('**** WARNING ****')

        nb = 26 + 2*(nmsub - 1)
        ng = 26 + 2*(nmsub - 1)

        sm=np.zeros([ng,nb,na],dtype=np.int32)
        xd=np.zeros(na,dtype=np.double)
        xh=np.zeros(nb,dtype=np.double)
        xl=np.zeros(ng,dtype=np.double)

        xh1_tot = np.sqrt(3838.0 / (vf * r)) - 69.0
        xxh1 = xh1_tot/nmsub

        xl1_tot = r * (69.0 + xh1_tot) - 69.0
        xxl1 = xl1_tot/nmsub

        for ii in range(nmsub+1):
            xh[ii-1] = xxh1
            xl[ii-1] = xxl1

        for ii in range(na):
            xd[ii]=sumd/na


        ishift = nmsub - 1

        xh[2 + ishift-1]= 2.0
        xh[3 + ishift-1]= 3.0
        xh[4 + ishift-1]= 4.0
        xh[5 + ishift-1]= 3.0
        xh[6 + ishift-1]= 4.0
        xh[7 + ishift-1]= 5.0
        xh[8 + ishift-1]= 5.0
        xh[9 + ishift-1]= 4.0
        xh[10 + ishift-1]= 6.0
        xh[11 + ishift-1]= 9.0
        xh[12 + ishift-1]= 7.0
        xh[13 + ishift-1]= 17.0

        for i in range(12 + nmsub - 1 + 1):
            xh[13 + nmsub - 1 + i] = xh[13 + nmsub - i-2]
            xl[13 + nmsub - 1 + i] = xh[13 + nmsub - 1 + i]
            xl[13 + nmsub - i-2] = xh[13 + nmsub - i-2]

        xl[26 + 2*(nmsub - 1)-1] = xl[1-1]
        xh[26 + 2*(nmsub - 1)-1] = xh[1-1]

        for ia in range(na):
            for ib in range(nb):
                for ig in range(ng):

                    sm[ig,ib,ia] = m

                    if ((ib+1 == 2 + ishift) or (ib+1 == 25 + ishift)):
                        if ((ig+1 >= 13 + ishift) and (ig+1 <= 14 + ishift)):
                            sm[ig,ib,ia] =f

                    elif ((ib+1 == 3 + ishift) or (ib+1 == 24 + ishift)):
                        if ((ig+1 >= 12 + ishift) and (ig+1 <= 15 + ishift)):
                            sm[ig,ib,ia] = f

                    elif ((ib+1 == 4 + ishift) or (ib+1 == 23 + ishift)):
                        if ((ig+1 >= 11 + ishift) and (ig+1 <= 16 + ishift)):
                            sm[ig,ib,ia] = f

                    elif ((ib+1 == 5 + ishift) or (ib+1 == 22 + ishift)):
                        if ((ig+1 >= 10 + ishift) and (ig+1 <= 17 + ishift)):
                            sm[ig,ib,ia] = f

                    elif ((ib+1 == 6 + ishift) or (ib+1 == 21 + ishift)):
                        if ((ig+1 >= 9 + ishift) and (ig+1 <= 18 + ishift)):
                            sm[ig,ib,ia] = f

                    elif ((ib+1 == 7 + ishift) or (ib+1 == 20 + ishift)):
                        if ((ig+1 >= 8 + ishift) and (ig+1 <= 19 + ishift)):
                            sm[ig,ib,ia] = f

                    elif ((ib+1 == 8 + ishift) or (ib+1 == 19 + ishift)):
                        if ((ig+1 >= 7 + ishift) and (ig+1 <= 20 + ishift)):
                            sm[ig,ib,ia] = f

                    elif ((ib+1 == 9 + ishift) or (ib+1 == 18 + ishift)):
                        if ((ig+1 >= 6 + ishift) and (ig+1 <= 21 + ishift)):
                            sm[ig,ib,ia] = f

                    elif ((ib+1 == 10 + ishift) or (ib+1 == 17 + ishift)):
                        if ((ig+1 >= 5 + ishift) and (ig+1 <= 22 + ishift)):
                            sm[ig,ib,ia] = f

                    elif ((ib+1 == 11 + ishift) or (ib+1 == 16 + ishift)):
                        if ((ig+1 >= 4 + ishift) and (ig+1 <= 23 + ishift)):
                            sm[ig,ib,ia] = f

                    elif ((ib+1 == 12 + ishift) or (ib+1 == 15 + ishift)):
                        if ((ig+1 >= 3 + ishift) and (ig+1 <= 24 + ishift)):
                            sm[ig,ib,ia] = f

                    elif ((ib+1 == 13 + ishift) or (ib+1 == 14 + ishift)):
                        if ((ig+1 >= 2 + ishift) and (ig+1 <= 25 + ishift)):
                            sm[ig,ib,ia] = f
    #------------------------------------------------------------------------
    ruc={}
    ruc['na']=na
    ruc['nb']=nb
    ruc['ng']=ng
    ruc['d']=xd
    ruc['h']=xh
    ruc['l']=xl
    ruc['sm']=sm

    return ruc

def get_builtin_ruc_2d(archid,vf,f,m,r,p):
    """
    function to set up built-in NASMAT 2D RUCs

    Parameters:
        archid (int): NASMAT *RUC ARCHID parameter for RUC
        vf (int): NASMAT *RUC VF parameter for RUC
        f (int): NASMAT *RUC F parameter for RUC
        m (int): NASMAT *RUC M parameter for RUC
        r (int): NASMAT *RUC R parameter for RUC
        p (int): NASMAT *RUC P parameter for RUC

    Returns:
        ruc (dict): ruc parameters
    """

    if archid==1:
        nb = 2
        ng = 2
        sm=np.ones([nb,ng],dtype=np.int32)*m
        sm[0][0] = f
        xh=np.zeros(nb,dtype=np.double)
        xl=np.zeros(ng,dtype=np.double)
        xh[0] = math.sqrt(vf)
        xh[1] = 1.0 - math.sqrt(vf)
        xl[0] = xh[0]
        xl[1] = xh[1]

    elif archid==2:
        nb=4
        ng=4

        sm=np.zeros([nb,ng],dtype=np.int32)
        xh=np.zeros(nb,dtype=np.double)
        xl=np.zeros(ng,dtype=np.double)

        vffac = 0.86602
        if vf > vffac:
            print('*** WARNING ***')
            print(f"ARCHID 2: MAXIMUM V_F EXCEEDED, USING MAX. OF {vffac}")
            vf = vffac

        if vf < 0.288675:
            xa = math.sqrt(math.sqrt(3.0) * vf /2.0)
            xb = (1.0 - xa) / 2.0
            xc = math.sqrt(3.0 / 4.0) - xa
            xh[0] = xb - xa / 2.0
            xh[1] = xa
            xh[2] = xb - xa / 2.0
            xh[3] = xa
            xl[0] = xa
            xl[1] = xc
            xl[2] = xa
            xl[3] = xc

            for ib in range(nb):
                for ig in range(ng):
                    #NS = ng * (ib - 1) + ig #orig - fortran
                    ns = ng * (ib) + ig + 1
                    if ns in (5,15):
                        sm[ib][ig] = f
                    else:
                        sm[ib][ig] = m

        else:
            xa = math.sqrt(math.sqrt(3.0) * vf / 2.0)
            xb = (1.0 - xa) / 2.0
            xc = math.sqrt(3.0 / 4.0) - xa

            xh[0] = 2.0 * xb
            xh[1] = xa / 2.0 - xb
            xh[2] = 2.0 * xb
            xh[3] = xa / 2.0 - xb
            xl[0] = xa
            xl[1] = xc
            xl[2] = xa
            xl[3] = xc

            for ib in range(nb):
                for ig in range(ng):
                    #NS = ng * (ib - 1) + ig #orig - fortran
                    ns = ng * (ib) + ig +1
                    if ns in (3,5,7,9,13,15):
                        sm[ib][ig] = f
                    else:
                        sm[ib][ig] = m

    #------------------------------------------------------------------------
    elif archid==6:

        nb = 7
        ng = 7
        sm=np.zeros([nb,ng],dtype=np.int32)
        xh=np.zeros(nb,dtype=np.double)
        xl=np.zeros(ng,dtype=np.double)
        if r > 1.0:
            vffac = (52.0 / 64.0) / r
        elif r < 1.0:
            vffac = r * (52.0 / 64.0)
        else:
            vffac = 52.0 / 64.0
        if vf > vffac:
            print(f"MAXIMUM VF EXCEEDED, USING MAX. OF {vffac}")
            vf = vffac
        radius = np.sqrt(vf/np.pi)
        xh[2-1] = np.sqrt(np.pi) * radius / np.sqrt(52.0)
        xh[3-1] = xh[2-1]
        xh[4-1] = 4.0 * xh[2-1]
        xh[5-1] = xh[2-1]
        xh[6-1] = xh[2-1]
        # NOTE: XBP -> 2-dir.; XCP -> 3-dir.
        rad = xh[4-1] / 2.0 + xh[5-1] + xh[6-1]
        xb = (radius / 2.0) * np.sqrt(np.pi * r / vf)
        xbp = xb - rad
        xc = xb / r
        xcp = xc - rad
        xh[7-1] = xcp
        xh[1-1] = xh[7-1]
        xl[7-1] = xbp
        xl[1-1] = xl[7-1]
        xl[2-1] = xh[2-1]
        xl[3-1] = xh[3-1]
        xl[4-1] = xh[4-1]
        xl[5-1] = xh[5-1]
        xl[6-1] = xh[6-1]
        for ib in range(nb):
            for ig in range(ng):
               #ns = ng * (ib - 1) + ig #orig - fortran
                ns = ng * (ib) + ig +1
                if ns in (11,17,18,19,23,24,25,26,27,31,32,33,39):
                    sm[ib,ig] = f
                else:
                    sm[ib,ig] = m
    #------------------------------------------------------------------------
    elif archid==13:

        if 'NMSUB' not in p.keys():
            p['NMSUB']=1

        nmsub=p['NMSUB']
        if r >= 1:
            if vf > 0.80613 / r:
                vf = 0.80613 / r
                print('**** WARNING ****')
                print(f"MAX VF EXCEEDED, USING MAX VALUE OF {vf}")
                print('**** WARNING ****')
        else:
            if vf > 0.80613 * r:
                vf = 0.80613 * r
                print('**** WARNING ****')
                print(f"MAX VF EXCEEDED, USING MAX VALUE OF {vf}")
                print('**** WARNING ****')
        nb = 26 + 2*(nmsub - 1)
        ng = 26 + 2*(nmsub - 1)

        sm=np.zeros([nb,ng],dtype=np.int32)
        xh=np.zeros(nb,dtype=np.double)
        xl=np.zeros(ng,dtype=np.double)
        xh1_tot = np.sqrt(3838.0 / (vf * r)) - 69.0
        xxh1 = xh1_tot/nmsub
        xl1_tot = r * (69.0 + xh1_tot) - 69.0
        xxl1 = xl1_tot/nmsub
        for ii in range(nmsub+1):
            xh[ii-1] = xxh1
            xl[ii-1] = xxl1
        ishift = nmsub - 1
        xh[2 + ishift-1]= 2.0
        xh[3 + ishift-1]= 3.0
        xh[4 + ishift-1]= 4.0
        xh[5 + ishift-1]= 3.0
        xh[6 + ishift-1]= 4.0
        xh[7 + ishift-1]= 5.0
        xh[8 + ishift-1]= 5.0
        xh[9 + ishift-1]= 4.0
        xh[10 + ishift-1]= 6.0
        xh[11 + ishift-1]= 9.0
        xh[12 + ishift-1]= 7.0
        xh[13 + ishift-1]= 17.0
        for i in range(12 + nmsub - 1 + 1):
            xh[13 + nmsub - 1 + i] = xh[13 + nmsub - i-2]
            xl[13 + nmsub - 1 + i] = xh[13 + nmsub - 1 + i]
            xl[13 + nmsub - i-2] = xh[13 + nmsub - i-2]
        xl[26 + 2*(nmsub - 1)-1] = xl[1-1]
        xh[26 + 2*(nmsub - 1)-1] = xh[1-1]
        for ib in range(nb):
            for ig in range(ng):
                sm[ib, ig] = m
                if ((ib+1 == 2 + ishift) or (ib+1 == 25 + ishift)):
                    if ((ig+1 >= 13 + ishift) and (ig+1 <= 14 + ishift)):
                        sm[ib, ig] = f
                elif ((ib+1 == 3 + ishift) or (ib+1 == 24 + ishift)):
                    if ((ig+1 >= 12 + ishift) and (ig+1 <= 15 + ishift)):
                        sm[ib, ig] = f
                elif ((ib+1 == 4 + ishift) or (ib+1 == 23 + ishift)):
                    if ((ig+1 >= 11 + ishift) and (ig+1 <= 16 + ishift)):
                        sm[ib, ig] = f
                elif ((ib+1 == 5 + ishift) or (ib+1 == 22 + ishift)):
                    if ((ig+1 >= 10 + ishift) and (ig+1 <= 17 + ishift)):
                        sm[ib, ig] = f
                elif ((ib+1 == 6 + ishift) or (ib+1 == 21 + ishift)):
                    if ((ig+1 >= 9 + ishift) and (ig+1 <= 18 + ishift)):
                        sm[ib, ig] = f
                elif ((ib+1 == 7 + ishift) or (ib+1 == 20 + ishift)):
                    if ((ig+1 >= 8 + ishift) and (ig+1 <= 19 + ishift)):
                        sm[ib, ig] = f
                elif ((ib+1 == 8 + ishift) or (ib+1 == 19 + ishift)):
                    if ((ig+1 >= 7 + ishift) and (ig+1 <= 20 + ishift)):
                        sm[ib, ig] = f
                elif ((ib+1 == 9 + ishift) or (ib+1 == 18 + ishift)):
                    if ((ig+1 >= 6 + ishift) and (ig+1 <= 21 + ishift)):
                        sm[ib, ig] = f
                elif ((ib+1 == 10 + ishift) or (ib+1 == 17 + ishift)):
                    if ((ig+1 >= 5 + ishift) and (ig+1 <= 22 + ishift)):
                        sm[ib, ig] = f
                elif ((ib+1 == 11 + ishift) or (ib+1 == 16 + ishift)):
                    if ((ig+1 >= 4 + ishift) and (ig+1 <= 23 + ishift)):
                        sm[ib, ig] = f
                elif ((ib+1 == 12 + ishift) or (ib+1 == 15 + ishift)):
                    if ((ig+1 >= 3 + ishift) and (ig+1 <= 24 + ishift)):
                        sm[ib, ig] = f
                elif ((ib+1 == 13 + ishift) or (ib+1 == 14 + ishift)):
                    if ((ig+1 >= 2 + ishift) and (ig+1 <= 25 + ishift)):
                        sm[ib, ig] = f
    #------------------------------------------------------------------------
    ruc={}
    ruc['na']=1
    ruc['nb']=nb
    ruc['ng']=ng
    ruc['h']=xh
    ruc['l']=xl
    ruc['sm']=sm

    return ruc


def _get_builtin_stackstows(ruc):
    """
    function to set up built-in NASMAT 3D RUCs

    Parameters:
        ruc (dict): input ruc used to search for built-in RUCs

    Returns:
        ms (dict): dict of all rucs/tows used in the model
    """

    ms={}
    mats=np.unique(ruc['sm']).astype(int).tolist()
    negmats=[i for i in mats if -17<i<0]
    if negmats:
        negmats.sort(reverse=True)
    else:
        return ms

    #update any missing keys with defaults
    if 'modtow' not in ruc.keys():
        ruc['modtow']=102 #GMC2D
    if 'archtow' not in ruc.keys():
        ruc['archtow']=1 #2D 2x2
    if 'ftow' not in ruc.keys():
        ruc['ftow']=1
    if 'mtow' not in ruc.keys():
        ruc['mtow']=2
    if 'itow' not in ruc.keys():
        ruc['itow']=3
    if 'ritow' not in ruc.keys():
        ruc['itow']=0 #ritow required if interface is given
        ruc['ritow']=0.0

    if 'd' not in ruc.keys():
        ruc['d']=np.asarray([1.0])

    stacks=[i for i in mats if -10<=i<0]
    tows=[i for i in mats if -16<=i<-10]

    #create new RUCS for stacks
    for msm in stacks:
        s={'mod':103,'archid':99,'msm':str(msm)} #GMC3D stack required
        s['na']=4
        s['nb']=1
        s['ng']=1
        t4=ruc['d'][0]/4
        t4=[t4 for _ in range(4)]
        s['d']=np.asarray(t4,dtype=np.double)
        s['h']=np.asarray([1.0],dtype=np.double)
        s['l']=np.asarray([1.0],dtype=np.double)
        s['sm']=np.ones([s['ng'],s['nb'],s['na']],dtype=int)
        if msm==-1:
            s['sm']*=-11
            s['sm'][0][0][2]=-12
            s['sm'][0][0][3]=-12
        elif msm==-2:
            s['sm']*=ruc['mtow']
            s['sm'][0][0][1]=-13
            s['sm'][0][0][2]=-13
        elif msm==-3:
            s['sm']*=ruc['mtow']
            s['sm'][0][0][1]=-14
            s['sm'][0][0][2]=-14
        elif msm==-4:
            s['sm']*=ruc['mtow']
            s['sm'][0][0][1]=-15
            s['sm'][0][0][2]=-15
        elif msm==-5:
            s['sm']*=ruc['mtow']
            s['sm'][0][0][1]=-16
            s['sm'][0][0][2]=-16
        elif msm==-6:
            s['sm']*=ruc['mtow']
            s['sm'][0][0][2]=-11
            s['sm'][0][0][3]=-11
        elif msm==-7:
            s['sm']*=ruc['mtow']
            s['sm'][0][0][0]=-12
            s['sm'][0][0][1]=-12
        elif msm==-8:
            s['sm']*=ruc['mtow']
            s['sm'][0][0][0]=-11
            s['sm'][0][0][1]=-11
        elif msm==-9:
            s['sm']*=ruc['mtow']
            s['sm'][0][0][2]=-12
            s['sm'][0][0][3]=-12
        elif msm==-10:
            s['sm']*=-12
            s['sm'][0][0][2]=-11
            s['sm'][0][0][3]=-11

        tm=np.unique(s['sm']).astype(int).tolist()
        tm=[i for i in tm if i!=ruc['mtow']]
        tows+=tm

        ms[str(msm)]=s

    tows=np.unique(np.asarray(tows)).tolist()
    tows.sort(reverse=True)

    for tow in tows:
        t=get_builtin_ruc_2d(ruc['archtow'],ruc['vftow'],
                               ruc['ftow'],ruc['mtow'],
                               ruc['ritow'],{})
        t['msm']=tow
        t['mod']=102
        t['na']=1
        ms[str(tow)]=t


    return ms


def _read_ruc_block(f,legacy):
    """
    function to read an RUC block within the *RUC keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read
        legacy (bool): flag to read legacy MAC/GMC files if True

    Returns:
        r (dict): parameters from keyword
    """

    rh={}
    r={}

    lp=f.tell()
    rh['lp']=lp
    # d=f.readline().lstrip().rstrip()
    # if d.startswith('#'):
    #     d=f.readline().lstrip().rstrip()
    d,r['comments']=read_line(f)

    if d.startswith('*') and not d.startswith('**'):
        return rh,-1

    r=get_param_update_dict(d,r,' ','=')
    mod=r['mod']

    if legacy:
        legacy_mod = {2:102, 3:103, 22:202, 13:203}
        mod=r['mod']=legacy_mod[r['mod']]

    if mod in (2,3): #setup for MT
        r['sm']=np.empty((1,2,1),dtype=np.int32)
        r['sm'][0,0,0]=r['f']
        r['sm'][0,1,0]=r['m']
        r['na']=1
        r['nb']=2
        r['ng']=1
        r['d']=np.asarray([1.0],dtype=float)
        r['h']=np.asarray([r['vf'],1-r['vf']],dtype=float)
        r['l']=np.asarray([1.0],dtype=float)

    elif mod==302: #setup for PHFGMC2D
        #TODO: set up input file processing for PHFGMC2D
        raise ValueError('ERROR: Input file processing for PHFGMC2D not set up!')

        # d,_=read_line(f)
        # r=get_param_update_dict(d,r,' ','=')
        # d,_=read_line(f)
        # r=get_param_update_dict(d,r,' ','=')

    else:
        archid=r['archid']
        dim=0
        ioff=0
        if mod in (102,202,302):
            dim=102
        elif mod in (103,203):
            dim=103

        if archid==99:
            d,_=read_line(f)
            n=[x.split('=') for x in d.split(' ')]
            if dim==102:
                ioff=1
                r['na']=1
            elif dim==103:
                ioff=0
                r['na']=int(n[0][1])

            r['nb']=int(n[1-ioff][1])
            r['ng']=int(n[2-ioff][1])

            if dim==103:
                d=get_after_eqsign(f)
                r['d']=np.asarray(d.split(','),dtype=np.double)
            d=get_after_eqsign(f)
            r['h']=np.asarray(d.split(','),dtype=np.double)
            d=get_after_eqsign(f)
            r['l']=np.asarray(d.split(','),dtype=np.double)
            if dim==103:
                #r['sm']=np.zeros([r['na'],r['nb'],r['ng']])
                r['sm']=np.zeros([r['ng'],r['nb'],r['na']])
                amin,amax,ainc=0,0,1
                if r['na']==1:
                    amin,amax,ainc=0,r['na'],1
                elif r['na']>1:
                    amin,amax,ainc=r['na']-1,-1,-1
                for g in range(r['ng']):
                    for a in range(amin,amax,ainc):
                        d=get_after_eqsign(f)
                        d=d.split(',')
                        for b in range(r['nb']):
							#r['sm'][a][b][g]=d[b]
                            r['sm'][g][b][a]=d[b]
            elif dim==102:
                r['sm']=np.zeros([r['nb'],r['ng']])
                if r['nb']==1:
                    amin,amax,ainc=0,r['nb'],1
                elif r['nb']>1:
                    amin,amax,ainc=r['nb']-1,-1,-1
                for b in range(amin,amax,ainc):
                    d=get_after_eqsign(f)
                    d=d.split(',')
                    for g in range(r['ng']):
                        r['sm'][b][g]=d[g]
        else:

            p={}

            #add parameters for function call below if not defined
            if 'r' not in r:
                r['r']=None
            if 'asp' not in r:
                r['asp']=None

            if dim==103:
                ruc=get_builtin_ruc_3d(archid,r['vf'],r['f'],r['m'],r['r'],r['asp'],p)
                r['na']=ruc['na']
                r['d']=ruc['d']
            elif dim==102:
                ruc=get_builtin_ruc_2d(archid,r['vf'],r['f'],r['m'],r['r'],p)
                r['na']=1

            #remove parameters if not needed
            if not r['r']:
                r.pop('r')
            if not r['asp']:
                r.pop('asp')

            r['nb']=ruc['nb']
            r['ng']=ruc['ng']
            r['h']=ruc['h']
            r['l']=ruc['l']
            r['sm']=ruc['sm']

        ft=f.tell()
        d,_=read_line(f)
        ds=d.split('=')
        f.seek(ft)
        if ds[0].lower()=='d1':
            d=get_after_eqsign(f)
            r['d1']=np.asarray(d.split(','),dtype=np.double)
            d=get_after_eqsign(f)
            r['d2']=np.asarray(d.split(','),dtype=np.double)
            d=get_after_eqsign(f)
            r['d3']=np.asarray(d.split(','),dtype=np.double)
            # print('d1 = ',r['d1'])

        if 'msm' not in r:
            r['msm']=0
    if 'msm' not in r:
        r['msm']=0
    msm=str(int(r['msm']))
    rh[msm]=r

    return rh,msm

def Read_RUC(f,basename,legacy=False):
    """
    function to read *RUC keyword

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        r (dict): parameters from keyword
    """

    r={}

    r['nrucs']=1
    ft=f.tell()
    d=f.readline().lstrip().rstrip().lower()
    if d.startswith('nrucs'):
        #N=[x.split('=') for x in d.split(' ')]
        r['nrucs']=int(d.split('=')[1])
    else:
        f.seek(ft)

    ft=f.tell()
    d=f.readline().lstrip().rstrip().lower()
    if d.startswith('crot'):
        crot_flag=int(d.split('=')[1])
    else:
        crot_flag=0
        f.seek(ft)

    if crot_flag==1:
        if os.path.exists(basename+'.rot'):
            r['crot']={}

            with open(basename+'.rot','r',encoding='utf-8') as g:
                d=g.readline().lstrip().rstrip()
                n_rucs=int(d)
                for _ in range(n_rucs):
                    d=g.readline().lstrip().rstrip().split(',')
                    rn=d[0]
                    nc=int(d[1])
                    if nc!=0:
                        r['crot'][rn]=[]
                        for _ in range(nc):
                            d=g.readline().lstrip().rstrip().split(',')
                            r['crot'][rn].append([int(d[0]),int(d[1]),int(d[2]),
                                                float(d[3]),float(d[4]),float(d[5])])
            # print('crot: ', r['crot'])
        else:
            QMessageBox.warning(None,"Warning",
                                    "NASMAT expecting CROT input, but ROT file not found! "+
                                    "Using default RUC orientations.")
            crot_flag=0

    #TODO: support legacy stack input
    # ft=f.tell()
    # d=f.readline().lstrip().rstrip().lower()
    # if d.startswith('vftow'):
    #     N=[x.split('=') for x in d.split(' ')]
    #     r['vftow']=np.asarray(N[0][1],dtype=np.double)
    #     r['xang']=np.asarray(N[1][1],dtype=np.double)
    #     r['modtow']=np.asarray(N[2][1],dtype=np.int32)
    #     r['archtow']=np.asarray(N[3][1],dtype=np.int32)
    #     r['ftow']=np.asarray(N[4][1],dtype=np.int32)
    #     r['mtow']=np.asarray(N[5][1],dtype=np.int32)
    # else:
    #     f.seek(ft)

    ruc_cnt=0
    r['rucs']={}
    rmap={}
    for i in range(r['nrucs']): #pylint: disable=W0612
        ruc_cnt+=1
        rbt,msm=_read_ruc_block(f,legacy)

        if 'd1' in rbt:
            print(rbt['d1'])
        if len(rbt.keys())>1:
            r['rucs'].update(rbt)
            rmap[msm]=str(ruc_cnt)

        ms = _get_builtin_stackstows(rbt[str(msm)])
        if ms:
            for key,val in ms.items():
                rr = {key: val}
                ruc_cnt+=1
                r['rucs'].update(rr)
                rmap[str(rr[key]['msm'])]=str(ruc_cnt)

    f.seek(rbt['lp'])
    del r['rucs']['lp']

    r['ruc_map']=rmap
    return r
