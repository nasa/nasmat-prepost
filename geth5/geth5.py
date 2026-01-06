""" class for getting NASMAT hdf5 results."""
import os
import time
import h5py
import numpy as np


def vfunc(name, obj):
    """
    visitor function required for h5py.visititems(). Update to
    display more types of interest.
      
    See description in h5py documentation
    https://docs.h5py.org/en/stable/high/group.html#h5py.Group.visititems

    Parameters:
        name (str): current test string found in h5 file.
        obj (str): h5py string for different objects.

    Returns
        None.
    """

    if isinstance(obj, h5py.Dataset):
        # obj is a dataset
        print(f"Dataset: {name}")
    else:
        # obj is a group
        print(f"obj: {name}")

class GetH5():
    """
    gets HDF5 files (*.h5) and results
    """
    def __init__(self,h5name='',visit=False, echo = True):
        """
        initialize class

        Parameters:
            h5name (str): h5 file name including extension.
            visit (bool): option to visit h5 file and print relevant information.
            echo (bool): option to control screen printing.
        
        Returns:
            None.
        """

        begin_time = time.time()
        #open h5 file
        print(f"Reading HDF5 file:{h5name}")
        self.h5name=h5name
        self.echo=echo
        self.file=h5py.File(self.h5name, "r")
        self._get_h5_struct()
        self.ninc=max(self.h5_struct['incs'])
        self.opts={}
        self.current_data=None
        self.has_macroapi=False
        self.elem_to_deck={}
        self.maxlev=len(self.file['NASMAT Data'])-1
        if 'MACROAPI MESH' in self.file:
            self.has_macroapi=True
            self.name=list(self.file['NASMAT INPUT DECKS'].keys())

            elems=self.file['MACROAPI MESH/Elements'][:,:2]
            elems[:,1]+=1
            elems=elems.astype(int) #pylint: disable=E1101
            self.elem_to_deck = {str(key): value-1 for key, value in zip(elems[:, 0], elems[:, 1])}

        else:
            self.name=[h5name[:-2]+'MAC']


        if visit:
            if self.echo:
                print(f"Starting visit of HDF5 file: {self.name}")
            self.file.visititems(vfunc)
            if self.echo:
                print('-'*50)

        end_time = time.time()
        elapsed_time = end_time - begin_time
        if self.echo:
            print(f"Total h5 setup time: {elapsed_time:.4f} seconds")

    def setup_mac(self):
        """
        creates mac dict based on h5 content

        Parameters:
            None.
        
        Returns:
            None.
        """

        start_time=time.time()
        all_mac={}
        iruc=0
        for n in self.name:
            m={}
            m['name']=n
            m['Ori']={} #not implemented yet...
            m['mat_map']={}
            m['ruc_map']={}

            if self.has_macroapi:
                grp='NASMAT INPUT DECKS/' + n
                rucs=self.get_rucs()
                print('warning: NASMAT PrePost only supports 1 MAC deck contained'
                                        ' within a MacroAPI-generated h5 file!')
                nmats = sum(1 for item in self.file[grp+'/NASMAT Materials']
                            if isinstance(self.file[grp+'/NASMAT Materials'][item], h5py.Group))
            else:
                rucs=self.get_rucs()
                nmats = sum(1 for item in self.file['NASMAT Materials']
                            if isinstance(self.file['NASMAT Materials'][item], h5py.Group))

            #create map of materials
            all_mats=[np.arange(1,nmats+1)]
            [all_mats.append(rucs[key]['sm'].flatten()) for key in rucs.keys()] #pylint: disable=W0106
            all_mats=np.unique(np.concatenate(all_mats)).astype(int)

            m['mat_map']={i:all_mats[i] for i in range(all_mats.shape[0])}
            m['rev_mat_map']={all_mats[i]:i for i in range(all_mats.shape[0])}


            all_mats = [ruc['msm'] for ruc in rucs.values()]
            m['ruc_map']={str(all_mats[i]) : str(i+1) for i in range(len(all_mats))}


            #re-mapping SM matrix -- may can be deleted later
            nmp={m['mat_map'][key] : int(key) for key in m['mat_map'].keys()}
            for key,item in rucs.items():
                rucs[key]['sm']=np.vectorize(nmp.get)(item['sm'])

            nmp={key : m['mat_map'][key] for key in m['mat_map'].keys()}

            m['ruc']={}
            m['ruc']['rucs']={}
            m['ruc']['nrucs']=len(rucs.keys())
            for i in rucs.keys():
                ruc=rucs[i]

                ruc['all_mats']=np.vectorize(nmp.get)(ruc['sm']).astype(int)
                ruc['all_mats_uniq'],ruc['all_mats_uniq_cnt']=np.unique(ruc['all_mats'],
                                                                return_counts=True)

                m['ruc']['rucs'][i]=ruc

            all_mac[str(iruc)]=m

            iruc+=1

        iruc=[1]
        rucid={}
        rucnum='0'
        self._get_rucid(rucnum,m['ruc']['rucs'],iruc,rucid,m['mat_map'])
        all_mac['rucid']=rucid


        end_time = time.time()
        elapsed_time = end_time - start_time
        if self.echo:
            print(f"Total mac setup time: {elapsed_time:.4f} seconds")


        return all_mac


    def get_rucs(self,start_grp=None):
        """
        constructs rucs dict 

        Parameters:
            start_grp (h5group): starting location in h5 file to get data
        
        Returns:
            rucs (dict): parameters for all RUCs in the model
        """

        rucs={}
        if not start_grp:
            start_grp=self.file

        search_list = []
        #This is VERY slow --- may search through entire file
        # start_grp.visititems(lambda name, obj:
        #                       self._find_paths_with_string(name, 'NASMAT RUCs', search_list))
        [search_list.append(path) for path in self.path_index if 'NASMAT RUCs' in path] #pylint: disable=W0106

        #ruc = [l for l in search_list if len(l.split('/'))==2]
        ruc = [l for l in search_list if l.split('/')[-1].startswith('RUC')]

        # group_names = [name for name in start_grp['NASMAT RUCs']
        #                   if isinstance(start_grp['NASMAT RUCs//%s'%name], h5py.Group)]
        # print('grps: ', group_names)

        ## Extract the ruc data
        rucs={str(start_grp[ruc[i]].attrs['MSM'][0]):
                    { 'sm': start_grp[ruc[i] + '/MATNUM'][()],
                      'd': start_grp[ruc[i] + '/D'][()],
                      'h': start_grp[ruc[i] + '/H'][()],
                      'l': start_grp[ruc[i] + '/L'][()],
                      'msm': start_grp[ruc[i]].attrs['MSM'][0],
                      'mod': start_grp[ruc[i]].attrs['MOD'][0],
                      'archid': start_grp[ruc[i]].attrs['ARCHID'][0],
                      'na': start_grp[ruc[i]].attrs['NA'][0],
                      'nb': start_grp[ruc[i]].attrs['NB'][0],
                      'ng': start_grp[ruc[i]].attrs['NG'][0]
                      } for i in range(len(ruc))}

        for key in rucs.keys():
            #reordering SM array for plotting
            if rucs[key]['mod'] in (103,203):
                rucs[key]['sm']=np.swapaxes(rucs[key]['sm'],0,2)
            elif rucs[key]['mod'] in (102,202):
                # rucs[key]['sm']=np.squeeze(rucs[key]['sm'].reshape(rucs[key]['nb'],
                #                       rucs[key]['ng'], 1).transpose(1, 0, 2))
                rucs[key]['sm']=np.squeeze(rucs[key]['sm'])
                # rucs[key]['sm']=rucs[key]['sm'].reshape(rucs[key]['nb'],
                #                       rucs[key]['ng'], 1).transpose(1, 0, 2)

            mod=rucs[key]['mod']
            if mod in (102,202):
                rucs[key]['DIM']='2D'
            elif mod in (103,203):
                rucs[key]['DIM']='3D'
            else:
                rucs[key]['DIM']='MT'

        #adding orientations if present
        ruckeys=list(rucs.keys())
        h5grps={}
        for path in self.path_index:
            for key in ruckeys:
                if f"MSM={key}," in path and "Level=0" not in path:
                    h5grps[key]=path
                    ruckeys.remove(key)
                    break
        if ruckeys:
            print('warning: one or more matches not found when trying to set orientations: ',
                    ruckeys)

        for key,val in h5grps.items():
            get_rot = True
            try:
                rot=self.get_data_by_str(val+'/ROT')[:]
            except KeyError:
                get_rot = False

            if get_rot:
                rot1=rot[:,:,:,:,:,:,0:3]
                rot2=rot[:,:,:,:,:,:,3:6]
                rot3=rot[:,:,:,:,:,:,6:9]
                if rucs[key]['DIM']=='2D':
                    nx,ny,nz = 1,rucs[key]['nb'],rucs[key]['ng']
                    idx=np.arange(nx * ny * nz).reshape(nz, ny, nx).transpose(1, 0, 2).flatten()
                    rot1 = rot1.reshape([nx*ny*nz,rot1.shape[-1]])[idx,:]
                    rot2 = rot2.reshape([nx*ny*nz,rot2.shape[-1]])[idx,:]
                    rot3 = rot3.reshape([nx*ny*nz,rot3.shape[-1]])[idx,:]
                else:
                    nsubs=rucs[key]['na']*rucs[key]['nb']*rucs[key]['ng']
                    rot1 = rot1.reshape([nsubs,rot1.shape[-1]])
                    rot2 = rot2.reshape([nsubs,rot2.shape[-1]])
                    rot3 = rot3.reshape([nsubs,rot3.shape[-1]])
                rucs[key]['ORI_X1']=rot1
                rucs[key]['ORI_X2']=rot2
                rucs[key]['ORI_X3']=rot3

                rucs[key]['ORI_X1_NORM']=np.sqrt(np.sum(rucs[key]['ORI_X1']**2,axis=1))
                rucs[key]['ORI_X2_NORM']=np.sqrt(np.sum(rucs[key]['ORI_X2']**2,axis=1))
                rucs[key]['ORI_X3_NORM']=np.sqrt(np.sum(rucs[key]['ORI_X3']**2,axis=1))

        return rucs

    # def get_map(self,start_grp=None): # not used
    #     svmap={}
    #     if not start_grp:
    #         start_grp=self.file

    #     search_list = []
    #     start_grp.visititems(lambda name, obj:
    #                       self._find_paths_with_string(name, 'NASMAT RUCs', search_list))
    #     RUC = [l for l in search_list if len(l.split('/'))==2]
    #     svmap={str(start_grp[RUC[i]].attrs['MSM'][0]):int(RUC[i].split(' ')[-1])
    #               for i in range(len(RUC))}
    #     print('map: ', svmap)

    def _get_rucid(self,rucnum,all_rucs,iruc,rucid,mat_map):
        """
        recursive function to calculate rucid parent/child relationships 

        Parameters:
            rucnum (str): ruc number
            all_rucs (dict): all ruc parameter data
            iruc (list): single int used for counting
            rucid (dict): parent/child relationships for different rucs
            mat_map (dict): translates from 0-based to actual material numbers
        
        Returns:
            None.
        """

        ruc=all_rucs[rucnum]
        child_rucid = np.full((ruc['na'], ruc['nb'], ruc['ng']), -1, dtype=int)
        parent_iruc = iruc[0]

        for ia in range(ruc['na']):
            for ib in range(ruc['nb']):
                for ig in range(ruc['ng']):
                    mat=-1
                    if ruc['DIM']=='2D':
                        mat=ruc['sm'][ib][ig]
                    elif ruc['DIM']=='3D':
                        mat=ruc['sm'][ig][ib][ia]
                    elif ruc['DIM']=='MT':
                        mat=ruc['sm'][ig][ib][ia]
                    matnum=mat_map[mat]
                    if matnum<0:
                        iruc[0]+=1
                        child_iruc = iruc[0]
                        child_rucid[ia, ib, ig] = child_iruc
                        self._get_rucid(str(matnum),all_rucs,iruc,rucid,mat_map)

        rucid[str(parent_iruc)] = child_rucid


    def _find_paths_with_string(self, name, search_string, found_paths):
        """
        function to find all paths with a substring 

        Parameters:
            name (str): object name
            search_str (str): substring to look for
            found_paths (list): list of matching paths
        
        Returns:
            None.
        """
        if search_string in name:
            found_paths.append(name)

    def collect_paths(self, name, obj):
        """
        visitor function to grab all paths from h5 file 

        Parameters:
            name (str): object name
            obj (various): h5 data object 
        
        Returns:
            None.
        """

        if isinstance(obj, h5py.Dataset):
            if name.startswith('NASMAT Data'):
                grp_path= "/".join(name.split("/")[:-1])
                self.path_list.add(grp_path)
            elif name.startswith('NASMAT Materials'):
                grp_path= "/".join(name.split("/")[:-2])
                self.path_list.add(grp_path)
            elif name.startswith('NASMAT RUCs'):
                grp_path= "/".join(name.split("/")[:-1])
                self.path_list.add(grp_path)
            elif name.startswith('NASMAT INPUT DECKS'):
                if 'NASMAT Materials' in name:
                    icut = -2
                else:
                    icut = -1
                grp_path= "/".join(name.split("/")[:icut])
                self.path_list.add(grp_path)

    def _get_h5_struct(self):
        """
        function determine h5 data structure 

        Parameters:
            None. 
        
        Returns:
            None.
        """

        s=self.h5_struct={}
        file=self.file

        if 'NASMAT Data' not in file.keys():
            print('Error with H5 file, no RUC data available!')
            return

        reset_paths = False #for debugging
        if "path_index" not in self.file or reset_paths:
            print('path_index not found in h5 file, creating and appending to file...')
            self.file.close()
            self.file=h5py.File(self.h5name, "a")
            if reset_paths and 'path_index' in self.file:
                del self.file['path_index']
            self.path_list = set()
            self.file.visititems(self.collect_paths)
            str_dtype = h5py.string_dtype(encoding='utf-8')
            grps=sorted(self.path_list)
            self.file.create_dataset("path_index", data=grps, dtype=str_dtype)
            self.file.close()
            self.file=h5py.File(self.h5name, "r")
            file=self.file


        pi = self.file["path_index"][:]
        self.path_index=[path.decode('utf-8') for path in pi]

        search_list = []
        search_list = [path for path in self.path_index if 'Parent' in path]


        ruc = [l for l in search_list if len(l.split('/'))==3]
        ruc.sort()

        s['msm'] = list(set(int(l.split(',')[2].split('=')[1]) for l in ruc))
        s['msm'].sort()
        s['LEV'] = list(set(int(l.split('=')[1].split('/')[0]) for l in ruc))
        s['TENSORS'] = set(l.split('/')[-1] for l in search_list)
        s['TENSORS'] = [l for l in s['TENSORS'] if not '=' in l]

        for l in search_list:
            if 'Inc=' in l:
                incstr=l
                break
        grp_str=os.path.dirname(incstr)

        incs=[grp_str + f"/Inc={i}" for i in range(1,len(file[grp_str])+1)]
        s['incs'] = np.linspace(1, len(file[grp_str]), len(file[grp_str]), dtype=int).tolist()
        times = [file[l].attrs['TIME'][0] for l in incs
                    if (len(l.split("Inc")) == 1 or "/" not in l.split("Inc")[1])]
        s['times'] = np.unique(np.array(times, dtype=float)).tolist()

    def _indices_from_ic(self,ic, nb, ng):
        """
        function to calculate subvol indices from ruc subvol index 

        Parameters:
            ic (int): ruc subvol index 
        
        Returns:
            ia,ib,ig (int): subvol indices in the 1-, 2-, and 3-directions
        """

        ig = (ic - 1) % ng + 1
        ib = ((ic - 1) // ng) % nb + 1
        ia = (ic - 1) // (nb * ng) + 1
        return ia, ib, ig


    def get_data_str(self,lvl,pid,msm,ic,nb,ng,ipa,ipb,ipg,inc,grp=None,ind=None):
        """
        function to manually construct h5 data string  

        Parameters:
            lvl (int): NASMAT level
            pid (int): parent ruc id
            msm (int): actual material number
            ic (int): ruc subvol index
            nb,ng (int): parent ruc parameters 
            ipa,ipb,ipg (int): integration point numbers in three directions
            inc (int): increment number
            grp (str): string to modify data location
            ind (list): list of ia,ib,ig indices for subvol
        
        Returns:
            h5str (str): string pointing to data location in h5 file.
        """

        hgrp='NASMAT Data/'
        if grp:
            hgrp=hgrp+grp+'/'
        hgrp=hgrp+f"Level={lvl}/"

        if not ind:
            ia,ib,ig=self._indices_from_ic(ic,nb,ng)
        else:
            ia,ib,ig=ind
            pstr=f"MSM={msm}, IA={ia}, IB={ib}, IG={ig}, IPA={ipa}, IPB={ipb}, IPG={ipg}"
            #find pid at level from msm, indices -> assumes group names are unique!!!

            #original method - visit function slow for large data sets,
            #                  visiting all items recursively
            # search_list = []
            # self.file[hgrp].visititems(lambda name,
            #                   obj: self.find_paths_with_string(name, pstr, search_list))
            # resall = [l for l in search_list if len(l.split('/'))==1]
            # # print('ind: ', ind)
            # # print('res: ', resall)
            # respt=resall[0]

            #new method
            respt=None
            for name in self.file[hgrp].keys():
                if pstr in name:
                    respt=name
                    break

            pid=int(respt.split(',')[0].split('=')[1])


        h5str=(hgrp
                +f"Parent RUCID={pid}, RUCDef MSM={msm}, IA={ia}, IB={ib}, IG={ig}, "
                +f"IPA={ipa}, IPB={ipb}, IPG={ipg}/Inc={inc}")
        #h5str=(f"NASMAT Data/Level={lvl}
        #       +'/Parent RUCID=1, RUCDef MSM=0, IA=1, IB=1, IG=1, IPA=1, IPB=1, IPG=1"
        #       +f"/Inc={inc+1}")
        return h5str

    def get_data_by_str(self,h5str):
        """
        function get h5 data based on string 

        Parameters:
            h5str (str): string pointing to specific h5 data
        
        Returns:
            h5py.Group or h5py.Dataset: returned h5 data
        """

        return self.file[h5str]

    def get_number_incs(self):
        """
        function to calculate number of increments 

        Parameters:
            None.
        
        Returns:
            nincs (int): number of increments in file
        """

        lo='Level=0/Parent RUCID=0, RUCDef MSM=0, IA=0, IB=0, IG=0, IPA=0, IPB=0, IPG=0'
        try:
            h5=self.file['NASMAT Data/'+lo]
        except KeyError:
            macro=next(iter(self.file['NASMAT Data'].keys()))
            h5=self.file[f"NASMAT Data/{macro}/"+lo]
        nincs = sum(1 for item in h5 if isinstance(h5[item], h5py.Group))
        return nincs

    def get_h5_fields(self):
        """
        function to get h5 fields for plotting 

        Parameters:
            None.
        
        Returns:
            list: field keys present in file
        """

        lo='Level=0/Parent RUCID=0, RUCDef MSM=0, IA=0, IB=0, IG=0, IPA=0, IPB=0, IPG=0/Inc=1'
        try:
            h5=self.file['NASMAT Data/'+lo]
        except KeyError:
            macro=next(iter(self.file['NASMAT Data'].keys()))
            newloc=f"NASMAT Data/{macro}/"+lo
            h5=self.file[newloc]
        return list(h5.keys())

    def get_h5_fields_api(self):
        """
        function to get h5 fields from macroapi for plotting  

        Parameters:
            None.
        
        Returns:
            list: field keys present in file
        """

        h5=self.file['MACROAPI RESULTS/Inc=0']
        return list(h5.keys())

    def get_components(self,var):
        """
        function to calculate number of increments 

        Parameters:
            var (str): variable name
        
        Returns:
            comp (list): components for a given field variable
        """

        comp=[]

        v6 = ['E','S','Stress', 'Strain', 'ALPHA', 'ME.Strain', 'TH.Strain', 'IN.Strain','Z']
        v3 = ['XX','YY','DISP']
        v1 = ['MATNUM', 'SRC', 'Ctemp','RUCID']

        if var in v6:
            comp=['11','22','33','23','13','12']
        elif var in v3:
            comp=['11','22','33']
        elif var in v1:
            comp=['1']
        elif var=='IND':
            comp=[str(i+1) for i in range(3)]
        elif var=='FAILDATA':
            comp=[str(i+1) for i in range(4)]
        elif var=='C':
            comp=['11','12','13','14','15','16','22','23','24','25','26',
                  '33','34','35','36','44','45','46','55','56','66']
        elif var=='DMG':
            comp = [str(i+1) for i in range(8)]
        elif var=='ROT':
            comp = [str(i+1) for i in range(9)]
        elif var=='State Variables':
            nvars = self.file['MACROAPI RESULTS/Inc=0/State Variables'].shape[1]
            comp = [str(i+1) for i in range(nvars)]
        else:
            print(f"Warning: requested h5 variable {var} not added in get_components function")
            comp=['1']

        #add other quantities of interest to be calculated
        comp.append('MAG')

        return comp
