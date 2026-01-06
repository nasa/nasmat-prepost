"""
Contains the primary data structures for NASMAT PrePost.
Allows data to be shared and accessed from mulitple classes.

To add new data for use internally, initialize it in the 
NASMAT_PrePost __init__ definition.
""" #pylint: disable=C0103
class NPP: #pylint: disable=C0302,R0903
    """Borg implementation of Singleton to share data among classes"""
    _shared_state = {}
    def __init__(self):
        """
        Initializes NPP class

        Parameters:
            None.
        
        Returns:
            None.
        """

        self.__dict__ = self._shared_state

class NASMATPrePost(NPP):
    """ Primary data structure for accessing and setting globally available data"""
    def __init__(self):
        """
        Initializes NASMAT_PrePost class

        Parameters:
            None.
        
        Returns:
            None.
        """

        NPP.__init__(self)
        NPP.nasmat={}
        NPP.cur_file=None
        NPP.cur_deck=None
        NPP.cur_result={'field':0,'comp':0,'mode':0}
        NPP.env=None
        NPP.hierarchy={'kw':{},'res':{}}
        NPP.vtk_settings={}
        NPP.npp_settings={}
        NPP.macroapi=False
        NPP.selected=None
        NPP.xy_plots={}
        NPP.updated_fields=False

    def get(self,istr):
        """
        gets approporiate NASMAT PrePost data

        Parameters:
            istr (str): string of data being set
        
        Returns:
            various: data associated with string
        """

        return getattr(self, istr, None)

    def set(self,istr,val):
        """
        sets approporiate NASMAT PrePost data

        Parameters:
            istr (str): string of data being set
            val (various): data to be set to class instance attribute
        
        Returns:
            None.
        """

        if hasattr(self, istr):
            setattr(self, istr, val)
