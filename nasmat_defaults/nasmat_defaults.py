"""Helper class for setting NASMAT defaults in UI"""

class nasmat_defaults(): #pylint: disable=C0103,R0903
    """Helper class for setting NASMAT defaults in UI"""
    def __init__(self):
        """
        initializes class

        Parameters:
            None.

        Returns:
            None.
        """

        self.mats=self._get_mats()
        self.failprops=self._get_failprops()


    def _get_mats(self):
        """
        function to get default materials

        Parameters:
            None.

        Returns:
            vtk_settings (dict): default vtk settings
        """

        mats={}
        #IM7 carbon fiber
        mats['IM7']={'comments':['IM7 Carbon Fiber']}
        mats['IM7']['m']=1
        mats['IM7']['cmod']=6
        mats['IM7']['matid']='U'
        mats['IM7']['matdb']=1
        mats['IM7']['el']=['262.2E3','11.8E3','0.17','0.21','18.9E3','-0.9E-6','9.0E-6']
        # mats['IM7']['k']=None
        #Glass
        mats['GLASS']={'comments':['Glass']}
        mats['GLASS']['m']=1
        mats['GLASS']['cmod']=6
        mats['GLASS']['matid']='U'
        mats['GLASS']['matdb']=1
        mats['GLASS']['el']=['73.0E3','73.0E3','0.22','0.22','29.918E3','5.0E-6','5.0E-6']
        # mats['GLASS']['k']=None
        #8552 Epoxy
        mats['8552 Epoxy']={'comments':['8552 Epoxy']}
        mats['8552 Epoxy']['m']=1
        mats['8552 Epoxy']['cmod']=6
        mats['8552 Epoxy']['matid']='U'
        mats['8552 Epoxy']['matdb']=1
        mats['8552 Epoxy']['el']=['4.67E3','4.67E3','0.45','0.45','1.61E3','42.0E-6','42.0E-6']
        # mats['8552 Epoxy']['k']=None

        return mats

    def _get_failprops(self):
        """
        function to get default failure props

        Parameters:
            None.

        Returns:
            vtk_settings (dict): default vtk settings
        """

        fs={}
        #IM7 carbon fiber
        fs['IM7']={'comments': ['IM7 Carbon FIber'], 'mat': 1, 'ncrit': 1, 'crits': {
            '0': {'crit': 1, 'x11': 4335, 'x22':113, 'x33':113, 'x23':128, 'x13':138, 'x12':138, 
                  'compr': 'DIF', 'xc11': 2608, 'xc22':354, 'xc33':354, 'action': 1}}} 
        #Glass
        fs['GLASS']={'comments': ['Glass Fiber'], 'mat': 1, 'ncrit': 1, 'crits': {
            '0': {'crit': 1, 'x11': 2358, 'x22':2358, 'x33':2358, 'x23':1000, 'x13':1000,  
                  'x12':1000,'compr': 'DIF', 'xc11': 1653, 'xc22':1653, 'xc33':1653, 'action': 1}}}         
        #8552 Epoxy
        fs['8552 Epoxy']={'comments': ['8552 Epoxy'], 'mat': 1, 'ncrit': 1, 'crits': {
            '0': {'crit': 1, 'x11': 59.4, 'x22':59.4, 'x33':59.4, 'x23':112, 'x13':112, 'x12':112, 
                  'compr': 'DIF', 'xc11': 259, 'xc22':259, 'xc33':259, 'action': 1}}}    

        return fs
