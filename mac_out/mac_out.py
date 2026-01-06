"""class for writing NASMAT keyword data to output file"""
import numpy as np

class mac_out(): #pylint: disable=C0103,R0903
    """
    mac_out - writes keyword data to *.MAC files
    """
    def __init__(self,keywords,name='tmp.MAC',str_cutoff=75):
        """
        initialize class

        Parameters:
        keywords (dict): dictionary containing MAC file keywords and values
        name (str): MAC file name including extension. The default is ''.
        str_cutoff (int): approximate length used to wrap strings 

        Returns:
        
        None.
        """

        if not name.endswith('.MAC') and not name.endswith('.mac'):
            raise ValueError(f"Error: *.MAC or *.mac files not given for file - {name}")

        self.kw=keywords
        self.filename=name
        self.str_cutoff=str_cutoff

        with open(name,'w', encoding='utf-8') as f:
            self.file=f
            if 'title' in self.kw.keys():
                f.write(self.kw['title']+'\n')

            self._write_print()
            self._write_constituents()
            self._write_ruc()
            self._write_mech_mulitphys(multiphys=False)
            self._write_mech_mulitphys(multiphys=True)
            self._write_boundary()
            self._write_therm()
            self._write_solver()
            self._write_failure_subcell()
            self._write_pdfa()
            self._write_hdf5()
            self._write_probtype()
            self._write_ext()
            self._write_xy()
            self._write_matlab()
            self.file.write('*END')

    def _write_str(self,string,delim=','):
        """
        function for writing a string to an output file

        Parameters:
        string (str): input string to write
        delim (str): delimeter to use for writing

        Returns:
        
        None.
        """

        f=self.file
        cutoff=self.str_cutoff

        cv=len(string)
        if cv<=cutoff:
            f.write(string)
        else:
            while cv>cutoff:
                #handle delim separated lists
                res = [i for i in range(len(string)) if string.startswith(delim,i)]
                for i in res:
                    if i-cutoff<0:
                        ind=0
                    else:
                        ind=i
                        break
                #handle case where no res found
                if not res:
                    ind = string.rfind(' ', 0, cutoff + 1)

                if ind!=0:
                    f.write(string[:ind+1]+'&\n ')
                    string=string[ind+1:]
                else:
                    f.write(string)
                    string=''
                cv=len(string)
            #write "leftovers" if present
            if string:
                f.write(string)

    def _write_comments(self,comments):
        """
        function for writing user comments to an output file

        Parameters:
        comments (list): list of strings to write to file

        Returns:
        
        None.
        """

        if comments:
            for i in comments:
                if not i.lstrip().startswith("#"):
                    self.file.write('#--'+i+'\n')
                else:
                    self.file.write(i+'\n')

    def _kw_one_line(self,d,pad=' '):
        """
        function for writing a one line of a NASMAT keyword

        Parameters:
        d (dict): input dict of all keywords to combine into a string
        pad (str): separator between keywords

        Returns:
        
        None.
        """

        s = []
        for key, value in d.items():
            if key=='comments':
                continue
            if isinstance(value, list) or isinstance(value,np.ndarray):
                value_str = ",".join(map(str, value))
            else:
                value_str = str(value)
            s.append(f"{key}={value_str}")
        s = pad+" ".join(s)+'\n'
        return s


    def _write_print(self):
        """
        function for writing *PRINT

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('print'):
            return
        f=self.file
        f.write('*PRINT\n')
        s=self._kw_one_line(self.kw['print'])
        self._write_str(s)

    def _write_constituents(self):
        """
        function for writing *CONSTITUENTS

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('constit'):
            return
        f=self.file
        kw = self.kw['constit']
        f.write('*CONSTITUENTS\n')
        f.write(f" NMATS={kw['nmats']}\n")
        for i in range(kw['nmats']):
            mat=kw['mats'][str(i+1)]
            self._write_comments(mat['comments'])
            if 'ntp' not in mat.keys(): #temp-independent props
                s=self._kw_one_line(mat)
                self._write_str(s)
            else: #temp-dependent properties
                p={i:mat[i] for i in mat.keys() if i in ['m','cmod','tref','matid','matdb']}
                s=self._kw_one_line(p)
                self._write_str(s)
                if mat['cmod']!=15:
                    order=['ntp','tem','ea','et','nua','nut','ga','alpa','alpt']
                else:
                    order=['ntp','tem','c11','c12','c13','c14','c15','c16',
                           'c22','c23','c24','c25','c26','c33','c34','c35',
                           'c36','c44','c45','c46','c55','c56','c66','alf1',
                           'alf2','alf3','alf4','alf5','alf6']

                for o in order:
                    s=self._kw_one_line({o:mat[o]},pad='  ')
                    self._write_str(s)


    def _write_ruc(self):
        """
        function for writing *RUC

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('ruc'):
            return
        f=self.file
        kw = self.kw['ruc']
        f.write('*RUC\n')
        # self._write_comments(kw['comments'])

        for key in self.kw['ruc']['rucs']:
            ruc=self.kw['ruc']['rucs'][key]
            if 'na' in ruc.keys() and ruc['na']==0:
                ruc.pop('na')

        l1={key:kw[key] for key in kw.keys() if key in ['nrucs']}
        s=self._kw_one_line(l1)
        self._write_str(s)

        if 'crot' in kw.keys() and kw['crot']:
            s=self._kw_one_line({'crot':1})
            self._write_str(s)
            with open(self.filename[:-4]+'.rot','w', encoding='utf-8') as g:
                crot=kw['crot']
                g.write(f"{len(crot.keys())}\n")
                for key in crot.keys():
                    c=crot[key]
                    g.write(f"{key},{len(c)}\n")
                    for i in c:
                        g.write(f"{i[0]},{i[1]},{i[2]},{i[3]},{i[4]},{i[5]}\n")

        for key in kw['rucs'].keys(): #error catching
            try:
                kw['rucs'][key].pop('all_mats')
            except KeyError:
                pass
            try:
                kw['rucs'][key].pop('all_mats_uniq')
            except KeyError:
                pass
            try:
                kw['rucs'][key].pop('all_mats_uniq_cnt')
            except KeyError:
                pass

        ruc=kw['rucs']['0']
        self._write_ruc_blk(ruc,add_msm=False)

        rucs={key:kw['rucs'][key] for key in kw['rucs'].keys() if key!='0' and int(key)<=-17}
        [self._write_ruc_blk(rucs[key]) for key in rucs.keys()] #pylint: disable=W0106


    def _write_ruc_blk(self,ruc,add_msm=True):
        """
        function for writing *RUC unit cells

        Parameters:
        None.

        Returns:
        
        None.
        """

        msm=ruc['msm']
        d={key:ruc[key] for key in ruc.keys() if key not in
                 ['msm','DIM','na','nb','ng','d','h','l','sm',
                  'ORI_X1', 'ORI_X2', 'ORI_X3', 'ORI_X1_NORM',
                    'ORI_X2_NORM', 'ORI_X3_NORM','d1','d2','d3',
                    'crot','child']}

        if add_msm:
            d2={'msm':msm}
            d2.update(d)
            d=d2
        if 'comments' in ruc:
            self._write_comments(ruc['comments'])
        s=self._kw_one_line(d)
        self._write_str(s)

        if 'archid' in ruc and ruc['archid']==99:
            self._write_archid99(ruc)

        if 'd1' in ruc.keys():
            s=self._kw_one_line({'d1':ruc['d1'].tolist()})
            self._write_str(s)
            s=self._kw_one_line({'d2':ruc['d2'].tolist()})
            self._write_str(s)
            s=self._kw_one_line({'d3':ruc['d3'].tolist()})
            self._write_str(s)

    def _write_archid99(self,ruc):
        """
        function for writing *RUC ARCHID=99 inputs

        Parameters:
        None.

        Returns:
        
        None.
        """

        if ruc['DIM']!='3D':
            if 'd' in ruc.keys():
                ruc.pop('d')
            if 'na' in ruc.keys():
                ruc.pop('na')
        d={key:ruc[key] for key in ruc.keys() if key in ['na','nb','ng']}

        s=self._kw_one_line(d)
        self._write_str(s)
        if ruc['DIM']=='3D':
            s=self._kw_one_line({'d':ruc['d'].tolist()})
            self._write_str(s)
        s=self._kw_one_line({'h':ruc['h'].tolist()})
        self._write_str(s)
        s=self._kw_one_line({'l':ruc['l'].tolist()})
        self._write_str(s)
        sm=ruc['sm'].astype(int).copy()

        if 'mat_map' in self.kw.keys():
            m = {key:self.kw['mat_map'][key] for key in self.kw['mat_map'].keys()}
            def map_to_new(x):
                return m.get(x, x)
            vmap = np.vectorize(map_to_new)
            sm = vmap(sm)

        if ruc['DIM']=='3D':
            if len(sm.shape)<3:
                sm=sm.reshape(ruc['ng'],ruc['nb'],ruc['na'])
            for g in range(ruc['ng']):
                self.file.write(f"# -- gamma = {g+1}\n")
                for a in range(ruc['na'], 0, -1):
                    # if ruc['nb']==1 and ruc['ng']==1:
                    #     print('sm: ', sm)
                    #     nstr=self._kw_one_line({'sm':sm[a-1].tolist()})
                    # else:
                    nstr=self._kw_one_line({'sm':sm[g,:,a-1].tolist()})
                    self._write_str(nstr)
        else:
            for b in range(ruc['nb']-1, -1, -1):
                nstr=self._kw_one_line({'sm':sm[b,:].tolist()})
                self._write_str(nstr)

    def _write_mech_mulitphys(self,multiphys=False):
        """
        function for writing *MECH and *MULTIPHYSICS

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('mech') and not multiphys:
            return
        if not self.kw.get('multiphysics') and multiphys:
            return
        f=self.file

        if multiphys:
            kw = self.kw['multiphysics']
            f.write('*MULTIPHYSICS\n')
        else:
            kw = self.kw['mech']
            f.write('*MECH\n')

        if 'comments' in kw.keys():
            self._write_comments(kw['comments'])

        l1={key:kw[key] for key in kw.keys() if key in ['lop','reftime','pbc']}
        s=self._kw_one_line(l1)
        self._write_str(s)

        for opt in kw['blocks'].keys():
            blk=kw['blocks'][opt]
            if 'comments' in blk.keys():
                self._write_comments(blk['comments'])
            s=self._kw_one_line(blk)
            self._write_str(s)

    def _write_therm(self):
        """
        function for writing *THERM

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('therm'):
            return
        f=self.file
        f.write('*THERM\n')
        s=self._kw_one_line(self.kw['therm'])
        self._write_str(s)

    def _write_boundary(self):
        """
        function for writing *BOUNDARY

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('boundary'):
            return
        f=self.file
        f.write('*BOUNDARY\n')
        l1={key:self.kw['boundary'][key] for key in self.kw['boundary'].keys() if key in ['name']}
        s=self._kw_one_line(l1)
        self._write_str(s)

        with open(self.filename[:-4]+'.dat','w', encoding='utf-8') as g:
            try:
                mech_bcs=self.kw['boundary']['mech_bcs']
            except KeyError:
                mech_bcs=[]
            try:
                vect_bcs=self.kw['boundary']['vect_bcs']
            except KeyError:
                vect_bcs=[]
            g.write(f"{len(mech_bcs)},{len(vect_bcs)}\n")
            for bc in mech_bcs:
                g.write(f"{bc[0]},{bc[1]},{bc[2]},{bc[3]},{bc[4]},{bc[5]},{bc[6]}\n")
            for bc in vect_bcs:
                g.write(f"{bc[0]},{bc[1]},{bc[2]},{bc[3]},{bc[4]},{bc[5]},{bc[6]}\n")

    def _write_solver(self):
        """
        function for writing *SOLVER

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('solver'):
            return
        f=self.file
        kw = self.kw['solver']
        f.write('*SOLVER\n')
        #self._write_comments(kw['comments'])
        d = {key:kw[key] for key in kw.keys() if key not in ['nleg','ninteg']}
        s=self._kw_one_line(d)
        self._write_str(s)
        d = {key:kw[key] for key in kw.keys() if key in ['nleg','ninteg']}
        s=self._kw_one_line(d)
        self._write_str(s)

    def _write_failure_subcell(self):
        """
        function for writing *FAILURE_SUBCELL

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('failsub'):
            return
        f=self.file
        kw = self.kw['failsub']
        f.write('*FAILURE_SUBCELL\n')
        s=self._kw_one_line({'nmat':kw['nmat']})
        self._write_str(s)
        for key in kw['mats'].keys():
            d=kw['mats'][key]
            m = {key:d[key] for key in d.keys() if key!='crits'}
            s=self._kw_one_line(m,pad='  ')
            self._write_str(s)
            for i in d['crits'].keys():
                crit=d['crits'][i]
                if 'ntemp' not in crit:
                    s=self._kw_one_line(crit,pad='  ')
                    self._write_str(s)
                else:
                    keys = ['crit','compr','action','ntemp']
                    c1 = {k:crit[k] for k in keys}
                    s=self._kw_one_line(c1,pad='  ')
                    self._write_str(s)
                    fields = [k for k in crit if k not in keys]
                    c2 = [{k: crit[k][i] for k in fields}
                                for i in range(crit['ntemp'])]
                    for row in c2:
                        s=self._kw_one_line(row,pad='  ')
                        self._write_str(s)

    def _write_pdfa(self):
        """
        function for writing *PDFA

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('pdfa'):
            return
        f=self.file
        kw = self.kw['pdfa']
        f.write('*PDFA\n')
        s=self._kw_one_line({'nmat':kw['nmat']})
        self._write_str(s)
        for key in kw['mats'].keys():
            d=kw['mats'][key]
            s=self._kw_one_line(d,pad='  ')
            self._write_str(s)


    def _write_hdf5(self):
        """
        function for writing *HDF5

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('hdf5'):
            return
        f=self.file
        kw = self.kw['hdf5']
        f.write('*HDF5\n')
        s=self._kw_one_line(kw)
        self._write_str(s)

    def _write_probtype(self):
        """
        function for writing *PROBLEM_TYPE

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('probtype'):
            return
        f=self.file
        kw = self.kw['probtype']
        f.write('*PROBLEM_TYPE\n')
        s=self._kw_one_line(kw)
        self._write_str(s)

    def _write_ext(self):
        """
        function for writing *EXTERNAL_SETTINGS

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('ext'):
            return
        f=self.file
        kw = self.kw['ext']
        f.write('*EXTERNAL_SETTINGS\n')
        d = {key:kw[key] for key in kw.keys() if key in ['mode','nids']}
        s=self._kw_one_line(d)
        self._write_str(s)
        d = {key:kw[key] for key in kw.keys() if key not in ['mode','nids']}
        s=self._kw_one_line(d)
        self._write_str(s)

    def _write_xy(self):
        """
        function for writing *XYPLOT

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('xy'):
            return
        f=self.file
        kw = self.kw['xy']
        f.write('*XYPLOT\n')
        s=self._kw_one_line({'freq':kw['freq']})
        self._write_str(s)
        for plt in ['macro','micro']:
            s=self._kw_one_line({plt:kw[plt][plt]})
            self._write_str(s)
            results=kw[plt]['results']
            for key in results.keys():
                res=results[key]
                s=self._kw_one_line(res,pad='  ')
                self._write_str(s)

    def _write_matlab(self):
        """
        function for writing *MATLAB

        Parameters:
        None.

        Returns:
        
        None.
        """

        if not self.kw.get('matlab'):
            return
        f=self.file
        kw = self.kw['matlab']
        f.write('*MATLAB\n')
        s=self._kw_one_line(kw)
        self._write_str(s)
