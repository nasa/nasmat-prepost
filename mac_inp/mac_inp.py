"""functions for reading MAC input files"""
import numpy as np
from util.get_model_hierarchy import get_model_hierarchy
from .Read_Constit import Read_Constit
from .Read_RUC import Read_RUC
from .Read_Print import Read_Print
from .Read_HDF5 import Read_HDF5
from .Read_Matlab import Read_Matlab
from .Read_XYPlot import Read_XYPlot
from .Read_ProbType import Read_ProbType
from .Read_External import Read_External
from .Read_Solver import Read_Solver
from .Read_Mech import Read_Mech
from .Read_Therm import Read_Therm
from .Read_FailureSubcell import Read_FailureSubcell
from .Read_PDFA import Read_PDFA
from .Get_MsRM_D import get_msrm_d

class mac_inp(): #pylint: disable=C0103
    """
    mac_inp - reads and extracts keyword data from *.MAC files
    """
    def __init__(self,name=None,raw_input=None,echo=True):
        """
        initializes class

        Parameters:
            name (str): MAC file name including extension.
            raw_input (list): strings containing raw NASMAT input
            echo (bool): flag to control echoing data to screen
            
        Returns:
            None.
        """
        if not name.endswith('.MAC') and not name.endswith('.mac'):
            raise ValueError(f"Error: *.MAC or *.mac files not given for file - {name}")

        self.name=name
        self.raw_input=raw_input
        self.echo=echo
        self._mac_inp_func()

    def _mac_inp_func(self): #pylint: disable=R0912,R0914,R0915
        """
        primary function for reading mac input files

        Parameters:
            None.

        Returns:
            None.
        """

        fname=self.name
        raw_input = self.raw_input
        echo = self.echo

        m={}
        m['name']=fname[:-4]

        if raw_input:
            m['raw_input']=raw_input
            with open(fname,'w', encoding='utf-8') as f:
                for line in m['raw_input']:
                    f.write(line)
        else:
            with open(fname,'r', encoding='utf-8') as f:
                m['raw_input']=f.readlines()

        with open(fname,'r', encoding='utf-8') as f:
            if echo:
                print(f"For {fname}, the following keywords are present:")
            d=f.readline().lstrip().rstrip().upper()

            if not d.startswith('*'):
                m['title']=d
                d=f.readline().lstrip().rstrip().upper()

            msrm={}
            while True:
                if d == '*CONSTITUENTS':
                    if echo:
                        print('*CONSTITUENTS found')
                    m['constit']=Read_Constit(f)
                elif d == '*RUC':
                    if echo:
                        print('*RUC found')
                    msrm=Read_RUC(f,fname[:-4])
                elif d == '*RUC_LEGACY':
                    if echo:
                        print('*RUC_LEGACY found')
                    msrm=Read_RUC(f,fname[:-4],legacy=True)
                elif d == '*MECH':
                    if echo:
                        print('*MECH found')
                    m['mech']=Read_Mech(f)
                elif d == '*MULTIPHYSICS':
                    if echo:
                        print('*MULTIPHYSICS found')
                    m['multiphysics']=Read_Mech(f)
                elif d == '*THERM':
                    if echo:
                        print('*THERM found')
                    m['therm']=Read_Therm(f)
                elif d == '*SOLVER':
                    if echo:
                        print('*SOLVER found')
                    m['solver']=Read_Solver(f)
                elif d in ('*FAILURE_SUBCELL','*FAILURE SUBCELL'):
                    if echo:
                        print('*FAILURE_SUBCELL found')
                    m['failsub']=Read_FailureSubcell(f)
                elif d == '*PDFA':
                    if echo:
                        print('*PDFA found')
                    m['pdfa']=Read_PDFA(f)
                elif d == '*PRINT':
                    if echo:
                        print('*PRINT found')
                    m['print']=Read_Print(f)
                elif d == '*HDF5':
                    if echo:
                        print('*HDF5 found')
                    m['hdf5']=Read_HDF5(f)
                elif d == '*PROBLEM_TYPE':
                    if echo:
                        print('*PROBLEM_TYPE found')
                    m['probtype']=Read_ProbType(f)
                elif d == '*EXTERNAL_SETTINGS':
                    if echo:
                        print('*EXTERNAL_SETTINGS found')
                    m['ext']=Read_External(f)
                elif d == '*XYPLOT':
                    if echo:
                        print('*XYPLOT found')
                    m['xy']=Read_XYPlot(f)
                elif d == '*MATLAB':
                    if echo:
                        print('*MATLAB found')
                    m['matlab']=Read_Matlab(f)

                d=f.readline()
                if not d: #handle case of blank lines between keywords
                    break
                d=d.lstrip().rstrip().upper()

        #assign dimension
        for key in msrm['rucs'].keys():
            ruc=msrm['rucs'][key]
            if ruc['mod'] in (102,202):
                msrm['rucs'][key]['DIM']='2D'
            elif ruc['mod'] in (103,203):
                msrm['rucs'][key]['DIM']='3D'
            else:
                msrm['rucs'][key]['DIM']='MT'

        #assign orientations
        #add orientations for all built-in materials
        for key in msrm['rucs'].keys():
            ruc=msrm['rucs'][key]
            mat=int(key)
            if -17 < mat < 0: #built in MSM
                d=get_msrm_d(mat,msrm['rucs']['0']['xang'])
                ruc.update(d)
        #assign orientations
        for key in msrm['rucs'].keys():
            ruc=msrm['rucs'][key]
            mat=int(key)
            sz=ruc['sm'].size
            ruc['ORI_X1'] = np.zeros((sz,3),dtype=float)
            ruc['ORI_X2'] = np.zeros((sz,3),dtype=float)
            ruc['ORI_X3'] = np.zeros((sz,3),dtype=float)
            if ruc['DIM']=='2D':
                sm=ruc['sm'].astype(int).flatten()
            elif ruc['DIM']=='3D':
                sm=ruc['sm'].astype(int).ravel()
            elif ruc['DIM']=='MT':
                sm=ruc['sm'].astype(int)

            neg_mats = np.unique(sm[sm<0]).astype(int)
            if neg_mats.size > 0:
                for mat in neg_mats:
                    if 'd1' in msrm['rucs'][str(mat)].keys():
                        neg_pos = sm==mat
                        ruc['ORI_X1'][neg_pos] = msrm['rucs'][str(mat)]['d1']
                        ruc['ORI_X2'][neg_pos] = msrm['rucs'][str(mat)]['d2']
                        ruc['ORI_X3'][neg_pos] = msrm['rucs'][str(mat)]['d3']
                        # ruc['ORI_X1'][neg_pos] = np.array([msrm['rucs'][val]['D1']
                        #   for val in str_mats[neg_pos] if 'D1' in msrm['rucs'][val].keys()])
                        # ruc['ORI_X2'][neg_pos] = np.array([msrm['rucs'][val]['D2']
                        #   for val in str_mats[neg_pos] if 'D2' in msrm['rucs'][val].keys()])
                        # ruc['ORI_X3'][neg_pos] = np.array([msrm['rucs'][val]['D3']
                        #   for val in str_mats[neg_pos] if 'D3' in msrm['rucs'][val].keys()])

            ruc['ORI_X1_NORM']=np.sqrt(np.sum(ruc['ORI_X1']**2,axis=1))
            ruc['ORI_X2_NORM']=np.sqrt(np.sum(ruc['ORI_X2']**2,axis=1))
            ruc['ORI_X3_NORM']=np.sqrt(np.sum(ruc['ORI_X3']**2,axis=1))

            # if key=='0':
            #     print('x1-ori: ', ruc['ORI_X1'])

        #update orientations if CROT is present
        if 'crot' in msrm:
            for key,new_ori in msrm['crot'].items():
                ruc=msrm['rucs'][key]
                sz=ruc['sm'].size
                sh=ruc['sm'].shape
                ruc['ORI_X1'] = np.zeros((sz,3),dtype=float)
                ruc['ORI_X2'] = np.zeros((sz,3),dtype=float)
                ruc['ORI_X3'] = np.zeros((sz,3),dtype=float)
                for ori in new_ori:
                    #extract nasmat subvolume indices
                    ia,ib,ig = ori[0:3]
                    #python index ordering
                    #2d: r['sm'][b][g], 3d: r['sm'][g][b][a]

                    #assuming d1, calculate other two vectors for coordinate system
                    d1=np.array(ori[3:])
                    if abs(d1[0])<1e-9: #fix for singularity in d2 calc
                        d1[0] = 1e-9
                    d2=np.array([-(d1[1]**2 +d1[2]**2)/d1[0],d1[1],d1[2]])
                    d3=np.array([0.0,-(d1[0]*d1[2] - d2[0]*d1[2]),
                                 d1[0]*d1[1] - d2[0]*d1[1]])
                    #convert all vectors into unit vectors
                    d1=d1/np.linalg.norm(d1)
                    d2=d2/np.linalg.norm(d2)
                    d3=d3/np.linalg.norm(d3)
                    #assign to appropriate position in ori array
                    iloc = -1
                    if ruc['DIM']=='2D':
                        iloc = (ib-1) * sh[1] + (ig-1)
                    elif ruc['DIM']=='3D':
                        iloc = (ig-1) * (sh[1] * sh[2]) + (ib-1) * sh[2] + (ia-1)

                    ruc['ORI_X1'][iloc]=d1
                    ruc['ORI_X2'][iloc]=d2
                    ruc['ORI_X3'][iloc]=d3

                ruc['ORI_X1_NORM']=np.sqrt(np.sum(ruc['ORI_X1']**2,axis=1))
                ruc['ORI_X2_NORM']=np.sqrt(np.sum(ruc['ORI_X2']**2,axis=1))
                ruc['ORI_X3_NORM']=np.sqrt(np.sum(ruc['ORI_X3']**2,axis=1))

        #Replace negative material numbers with positive
        all_mats=[np.arange(1,m['constit']['nmats']+1)]
        [all_mats.append(msrm['rucs'][key]['sm'].flatten()) for key in msrm['rucs'].keys()] #pylint: disable=W0106
        all_mats=np.unique(np.concatenate(all_mats)).astype(int)
        msrm['mat_map']={i:all_mats[i] for i in range(all_mats.shape[0])}
        msrm['rev_mat_map']={all_mats[i]:i for i in range(all_mats.shape[0])}

        for key in msrm['rucs'].keys():
            sm=msrm['rucs'][key]['sm']
            sm=sm.astype(int)
            vmapf = np.vectorize(msrm['rev_mat_map'].get)
            msrm['rucs'][key]['sm']=vmapf(sm)
            msrm['rucs'][key]['all_mats']=sm
            msrm['rucs'][key]['all_mats_uniq'],\
                msrm['rucs'][key]['all_mats_uniq_cnt']=np.unique(sm, return_counts=True)


    	#store values to be returned
        m['mat_map']=msrm['mat_map']
        m['rev_mat_map']=msrm['rev_mat_map']
        m['ruc_map']=msrm['ruc_map']
        # print('map: ', msrm['ruc_map'])

        m['ruc']={key:val for key,val in msrm.items()
                if key not in ['mat_map','rev_mat_map','ruc_map']}

        m['hierarchy']={}
        m['hierarchy']['kw']={}
        m['hierarchy']['kw']['hrchy'],m['hierarchy']['kw']['hrchy_items'],\
            _=get_model_hierarchy(m,True)
        m['hierarchy']['res']={}
        m['hierarchy']['res']['hrchy'],m['hierarchy']['res']['items'],_=get_model_hierarchy(m,False)

        # print('res hierarchy: ', m['hierarchy']['res']['hrchy'])
        # print('res item: ', m['hierarchy']['res']['items'])
        self.mac = m
