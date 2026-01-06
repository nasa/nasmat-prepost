"""Class for getting converting a single unit cell to RUC stacks """
import numpy as np
from tqdm import tqdm

class Stackify():
    """
    Stackify - utility function for converting a 3D unit cell to columns of 3D unit cells (stacks)
    """
    def __init__(self,rucs=None,stack_dir=1,lev0_mod=103,stack_mod=103,nmats=None,
                 crot=None,combine_stacks=None,rem_dup=False):
        """
        Initialize class.

        Parameters:
            rucs (dict): all RUCs in the model
            stack_dir (int): stack direction - currently only set up to work with stacks 
                             in the x1-direction (stack_dir=1)
            lev0_mod (int): NASMAT *RUC MOD parameter for highest level model
            stack_mod (int): NASMAT *RUC MOD parameter for individual stacks
            nmats (int): NASMAT *CONSTITUENT NMATS parameter, total number of constituents
            crot (list): NASMAT CROT input, only required for defining orientations (e.g., tows)
            combine_stacks (dict, optional): dict containing index ranges of stacks 
                                             to combine, keys can only be 'g' currently
                format: combine_stacks = {'g': [[1,3],[6,8]]} -
                        combines g=1-3 and g=6-8 into a single stack each
            rem_dup (bool, optional): flag to remove duplicate stacks - may slow down setup a lot
                                      not really needed with new crot input in NASMAT       

        Returns:
            None.
        """

        if not rucs:
            raise ValueError("rucs dictionary cannot be empty")
        if stack_dir!=1:
            raise ValueError("stack_dir currently only permitted to have a value of 1")
        if not nmats:
            raise ValueError("nmats must be defined")

        self.rucs=rucs
        self.stack_dir=stack_dir
        self.lev0_mod=lev0_mod
        self.stack_mod=stack_mod
        self.nmats=nmats
        self.crot=crot
        self.combine_stacks=combine_stacks
        self.rem_dup=rem_dup

        self.mapping={}
        self.stacks={}
        self.newrucs={}
        self.newglob = None
        self.newcrot = None

        self._convert()


    def _convert(self):
        """
        function to converts input ruc to stack format

        Parameters:
            None.      

        Returns:
            None.
        """
        glob=self.rucs['0']

        sc=0
        if self.stack_dir==1:
            newglob={}
            if np.float64==glob['d'].dtype:
                newglob['d']=np.array([np.sum(glob['d'])])
            else:#parameter expression
                p=[i.replace('{','').replace('}','') for i in glob['d']]
                newglob['d']=np.array(['{'+'+'.join(p)+'}'])


            newglob['na']=1
            newglob['nb']=glob['nb']
            newglob['ng']=glob['ng']
            newglob['mod']=self.lev0_mod
            newglob['sm']=np.zeros([newglob['ng'],newglob['nb'],newglob['na']])
            newglob['h']=glob['h']
            newglob['l']=glob['l']
            newglob['msm']=0
            newglob['archid']=99
            newglob['DIM']=str(self.lev0_mod)[2]+'D'
            for b in range(glob['nb']):
                for g in range(glob['ng']):
                    s=self.stacks[str(sc)]={}
                    s['d']=glob['d']
                    s['h']=np.array([glob['h'][b]])
                    s['l']=np.array([glob['l'][g]])
                    s['na']=glob['na']
                    s['nb']=1
                    s['ng']=1
                    s['sm']=glob['sm'][g:g+1,b:b+1,:]
                    s['mod']=self.stack_mod
                    s['archid']=99
                    s['DIM']=str(self.stack_mod)[2]+'D'
                    newglob['sm'][g,b,0]=sc
                    sc+=1

        elif self.stack_dir==2:
            #TODO: add stack_dir=2 support
            raise NotImplementedError('stack_dir=2 is not implemented yet.')
        elif self.stack_dir==3:
            #TODO: add stack_dir=3 support
            raise NotImplementedError('stack_dir=3 is not implemented yet.')

        self.newglob=newglob

        if self.rem_dup:
            pass #not tested recently
            # print('Removing stack duplicates...')
            # self.stacks,newglob['sm']=self.rem_dups(self.stacks,newglob['sm'])
            # self.newglob=newglob

        if self.combine_stacks and self.stack_dir==1:
            #TODO: verify logic to comine stacks, not tested recently
            raise NotImplementedError('The feature to combine stacks is not implemented yet.')
            # self._combine_all_stacks()

        self._update_rucs()
        self._set_mapping()


    def _combine_all_stacks(self):
        """
        function to combine stacks based on input

        Parameters:
            None.      

        Returns:
            None.
        """
        newglob=self.newglob
        glob=self.rucs['0']

        # newglob['l']=newglob['l'].astype('U256')
        # glob['l']=glob['l'].astype('U256')
        if 'b' in self.combine_stacks.keys():
            raise NotImplementedError('This feature to combine stacks is not implemented yet.')
        if 'g' in self.combine_stacks.keys():
            del_list=[]
            cur_max=max(int(s) for s in self.stacks.keys())
            for c in tqdm(self.combine_stacks['g'],
                        desc='Combining stacks - g: ',
                        total=len(self.combine_stacks['g'])):
                s=c[0]
                e=c[1]+1
                #update global d
                if np.float64==glob['l'].dtype:
                    newglob['l'][s]=np.sum(glob['l'][s:e])
                else:#parameter expression
                    p=[i.replace('{','').replace('}','') for i in glob['l'][s:e]]
                    newglob['l'][s]='{'+'+'.join(p)+'}'
                del_list+=list(range(s+1,e))
                for b in range(newglob['nb']):
                    cur_max+=1 #new global stack number
                    newglob['sm'][s,b]=cur_max
                    st=self.stacks[str(cur_max)]={}
                    st['l']=glob['l'][s:e]
                    st['d']=glob['d']
                    st['h']=np.array([glob['h'][b]])
                    st['na']=glob['na']
                    st['nb']=1
                    st['ng']=st['l'].shape[0]
                    st['sm']=np.zeros([st['ng'],st['nb'],st['na']])
                    st['mod']=self.stack_mod
                    st['msm']=str(cur_max)
                    for g in range(st['ng']):
                        st['sm'][g:g+1,0:1,:]=glob['sm'][s+g:s+g+1,b:b+1,:]
                    #check for duplicates, condense
                    dup=False
                    if self.rem_dup:
                        dup=True
                        for g in range(st['ng']-1):
                            if not np.array_equal(st['sm'][g,0,:],st['sm'][g+1,0,:]):
                                dup=False
                                break

                    if dup:
                        if np.float64==glob['d'].dtype:
                            st['l']=[np.sum(glob['l'][s:e])]
                        else:#parameter expression
                            p=[i.replace('{','').replace('}','') for i in st['l']]
                            st['l']=np.array(['{'+'+'.join(p)+'}'])
                        st['ng']=st['l'].shape[0]
                        st['sm'] = st['sm'][0:1,0:1,:]

            # print('subvol indices to combine: ',self.combine_stacks)
            del_list=[i for i in del_list if i+1<=newglob['ng']]
            # print('deleting g = ', del_list)
            newglob['l']=np.delete(newglob['l'],del_list)
            newglob['ng']=newglob['l'].shape[0]
            newglob['sm'] = np.delete(newglob['sm'], del_list, axis=0)
            stacks,newglob['sm']=self._rem_dups(self.stacks,newglob['sm'])

            self.stacks=stacks

        self.newglob=newglob


    def _update_rucs(self):
        """
        function to get updated ruc data for stack model

        Parameters:
            None.      

        Returns:
            None.
        """

        stacks=self.stacks
        newglob=self.newglob

        newsm={}
        #re-map glob sm
        ic=-17
        for key in stacks.keys():
            newsm[key]=ic #key - stack id, value - new id
            newglob['sm'][newglob['sm']==float(key)]=ic
            ic-=1

        # Begin creating new ruc dict
        newrucs={'0':newglob}
        # re-map stack sm/Msm, add to newrucs
        for key in stacks.keys():
            stacks[key]['msm']=newsm[key]
            newrucs[str(int(newsm[key]))]=stacks[key]

        #re-map old rucs (not glob) sm/Msm/F/M, add to newrucs
        sm_map={str(i):i for i in range(self.nmats+1)}
        for key in self.rucs.keys():
            if key=='0':
                continue
            n=newrucs[str(ic)]=self.rucs[key].copy()
            sm_map[key]=float(ic)
            print(f"MSM: old={key},new={ic}")

            if not 'raw_input' in n.keys():
                pass #new stacks updated below

            else:
                #built-in RUC
                ival=n['raw_input'].lstrip().rstrip().split(' ')
                ri=[]
                for i in ival:
                    chk=False
                    il=i.lower().split('=')
                    if il[0]=='msm' or il[0]=='f' or il[0]=='m':
                        chk=True
                    if chk and il[1] in sm_map.keys():
                        ri.append(il[0]+'='+str(int(sm_map[il[1]])))
                    else:
                        ri.append(i)
                n['raw_input']=' '+' '.join(ri)

            ic-=1

        #Update stacks sm
        kls=[int(i) for i in sm_map.keys()]
        kls.sort()
        kls=[str(i) for i in kls]
        for key,n in newrucs.items():
            if key=='0':
                continue
            if 'raw_input' not in n.keys():
                for key2 in kls:
                    #n['Msm']=sm_map[key2]
                    if 'sm' in n:
                        n['sm'][n['sm']==float(key2)]=sm_map[key2]
                    else:
                        if n['f']==int(key2):
                            n['m']=sm_map[key2]
                        if n['m']==int(key2):
                            n['m']=sm_map[key2]

        #Catching previous Msms
        for key,val in newrucs.items():
            if key!='0':
                if 'msm' in val.keys():
                    if val['msm']!=key:
                        val['msm']=int(key)

        stk=['d','h','l']
        if self.lev0_mod in (102,202):
            newrucs['0']['mod']=self.lev0_mod
            newrucs['0'][stk[self.stack_dir-1]]=[]
            newrucs['0']['sm']=np.transpose(newrucs['0']['sm'][:,:,0])

        crot_st={}
        if self.crot:
            na=self.rucs['0']['na']
            nb=self.rucs['0']['nb']
            ng=self.rucs['0']['ng']
            oris=np.zeros((na,nb,ng,3),dtype=float)
            for c in self.crot:
                oris[c[0]-1,c[1]-1,c[2]-1,:]=np.asarray([c[3],c[4],c[5]])

            for ib in range(nb):
                for ig in range(ng):
                    a=oris[:,ib,ig,:]
                    # mask=np.any(a!=0, axis=1)
                    crot_tmp=[]
                    for ia in range(na):
                        o=a[ia,:]
                        if np.any(o!=0):
                            crot_tmp.append([ia+1,1,1,o[0],o[1],o[2]])
                    if crot_tmp:
                        if newrucs['0']['DIM']=='3D':
                            mat_key = str(int(newrucs['0']['sm'][ig,ib,0]))
                        else:
                            mat_key = str(int(newrucs['0']['sm'][ib,ig]))

                        crot_st[mat_key]=crot_tmp

            for key, ruc in newrucs.items():
                if key in crot_st:
                    rcrot = crot_st[key]
                    sz=ruc['sm'].size
                    sh=ruc['sm'].shape
                    ruc['ORI_X1'] = np.zeros((sz,3),dtype=float)
                    ruc['ORI_X2'] = np.zeros((sz,3),dtype=float)
                    ruc['ORI_X3'] = np.zeros((sz,3),dtype=float)

                    for ori in rcrot:
                        #extract nasmat subvolume indices
                        ia,ib,ig = ori[0:3]
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
                        iloc = (ig-1) * (sh[1] * sh[2]) + (ib-1) * sh[2] + (ia-1)
                        ruc['ORI_X1'][iloc]=d1
                        ruc['ORI_X2'][iloc]=d2
                        ruc['ORI_X3'][iloc]=d3

                    ruc['ORI_X1_NORM']=np.sqrt(np.sum(ruc['ORI_X1']**2,axis=1))
                    ruc['ORI_X2_NORM']=np.sqrt(np.sum(ruc['ORI_X2']**2,axis=1))
                    ruc['ORI_X3_NORM']=np.sqrt(np.sum(ruc['ORI_X3']**2,axis=1))


        self.newrucs=newrucs
        self.newcrot=crot_st

    def _rem_dups(self,stacks,glob_sm):
        """
        function to remove/replace duplicate stacks

        Parameters:
            stacks (dict): dict of all stacks in the model
            glob_sm (np.ndarray): material arrangement matrix for ruc
        
        Returns:
            stacks (dict): updated dict of all stacks in the model
            glob_sm (np.ndarray): updated material arrangement matrix for ruc
        """

        dup_stk={}
        dup_found=True
        while dup_found:
            dup_found=False
            dups=[]
            master_key = None
            # for key in stacks.keys():
            for key in tqdm(stacks.keys(),desc='Looking at stacks: ', total=len(stacks.keys())):
                if dups:
                    dup_found=True
                    break
                for key2 in stacks.keys():
                    dup=self._id_dup(stacks[key],stacks[key2])
                    if dup and key!=key2:
                        master_key=key
                        dups.append(key2)

            if dups:
                dup_stk[master_key]=dups
                for i in dups:
                    glob_sm[glob_sm==float(i)]=master_key
                [stacks.pop(k) for k in dups] #pylint: disable=W0106

        return stacks,glob_sm


    def _id_dup(self,d1,d2):
        """
        function to identify duplicate stacks

        Parameters:
            d1,d1 (dict): two stacks to compare

        Returns:
            bool: flag to tell if two stacks are the same
        """

        if d1['na']!= d2['na']:
            return False
        if d1['nb']!= d2['nb']:
            return False
        if d1['ng']!= d2['ng']:
            return False
        if d1['mod']!= d2['mod']:
            return False

        return all(np.array_equal(d1[arr], d2[arr]) for arr in ['d','h','l','sm'])

    def _set_mapping(self):
        """
        function to update several mapping dicts

        Parameters:
            None.

        Returns:
            None.
        """

        all_mats=[np.arange(1,self.nmats+1)]
        [all_mats.append(val['sm'].flatten()) for key,val in self.newrucs.items()] #pylint: disable=W0106
        all_mats=np.unique(np.concatenate(all_mats)).astype(int)
        all_rucs = [ruc['msm'] for ruc in self.newrucs.values()]

        self.mapping['mat_map']={i:all_mats[i] for i in range(all_mats.shape[0])}
        self.mapping['rev_mat_map']={all_mats[i]:i for i in range(all_mats.shape[0])}
        self.mapping['ruc_map']={str(all_mats[i]) : str(i+1) for i in range(len(all_rucs))}
