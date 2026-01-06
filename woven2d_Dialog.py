"""class and functions handling 2D weave UI""" # pylint: disable=C0103
import numpy as np
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication,QDialog,QWidget # pylint: disable=E0611
from PyQt5.QtCore import Qt # pylint: disable=E0611
from vtk.util.numpy_support import vtk_to_numpy #pylint: disable=E0401,E0611
from NASMAT_PrePost import NASMATPrePost
from util.get_default_vtk_settings import get_default_vtk_settings
from util.stackify import Stackify


class woven2d_Dialog(QDialog): #pylint: disable=C0103,R0902
    """Class for the woven2d_Dialog UI."""
    def __init__(self,parent=None,mats=None):
        """
        Initialization routine called for the woven2d_Dialog class.

        Parameters:
            parent (class): self from parent calling this class
            mats (list): strings of available material numbers 

        Returns:
            None.
        """

        super().__init__(parent)
        loadUi("ui/woven2d_Dialog.ui", self)

        vsi=get_default_vtk_settings()
        vsi['PlotMode'] = 'Woven2D'
        vsi['hover']=False
        vsi['show_axes']=False
        vsi['rotate_grid']=False

        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        vs[id(self)]=vsi
        npp.set('vtk_settings',vs)
        npp.set('selected',self)

        self.last_weave='None'
        self.final_ruc={}
        self.cur_ui_vals={}
        self.nmats=len(mats)
        self.get_sm=False

        self.set_2dwoven_sub()

        if mats:
            self.woven_warp_mat.clear()
            self.woven_warp_mat.addItems(mats)
            self.woven_weft_mat.clear()
            self.woven_weft_mat.addItems(mats)
            self.woven_Mmat.clear()
            self.woven_Mmat.addItems(mats)

            self.woven_warp_mat.setCurrentIndex(0)
            if len(mats)>2:
                self.woven_Mmat.setCurrentIndex(2)
                self.woven_weft_mat.setCurrentIndex(1)
            else:
                self.woven_Mmat.setCurrentIndex(1)
                self.woven_weft_mat.setCurrentIndex(0)

    def keyPressEvent(self, event): #pylint: disable=C0103
        """
        Key press event handler

        Parameters:
            event (QEvent): triggered event from key press

        Returns:
            None.
        """

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Ignore Enter, particularly for QLineEdit (exits UI)
            event.ignore()
            return
        super().keyPressEvent(event)

    def _update_vtk(self):
        """
        Function to update vtk graphics.

        Parameters:
            None.

        Returns:
            None.
        """

        vtk_widget=self.findChild(QWidget, "vtk_widget")
        vtk_widget.update()

    def save_2dwoven_ruc(self):
        """
        Callback function to save 2d woven ruc.

        Parameters:
            None.

        Returns:
            None.
        """

        self.get_ui_vals()
        cv=self.cur_ui_vals
        t=cv['t']
        d=cv['d']
        tanx=0.5*t/d

        #update sm in case values changed in widget
        vtk_widget=self.findChild(QWidget, "vtk_widget")
        mats=vtk_to_numpy(vtk_widget.grid.GetCellData().GetArray('SM'))
        self.ruc['sm']=mats.reshape(self.ruc['sm'].shape,order='F')
        # lump first and last row/col into last value due to periodicity
        smw=self.ruc['sm'][1:,1:].copy() #nb,ng, 1-weft, 2-warp, 3-matrix

        nb,ng=smw.shape
        na=4
        sm=3*np.ones((ng,nb,na),dtype=int) #assign matrix (coded val, 3) to all cells
        oris=np.zeros((ng,nb,na,3),dtype=np.float64)

        n_weft=int(ng/2)
        n_warp=int(ng/2)

        r={}
        r['ng'],r['nb'],r['na']=sm.shape
        r['d']=self.ruc['d']
        r['h']=self.ruc['h'][1:]
        r['h'][-1]*=2
        r['l']=self.ruc['l'][1:]
        r['l'][-1]*=2

        #Assign flat section tows
        for i in range(n_warp):
            for j in range(n_weft):
                if smw[2*i,2*j]==1: #weft tow on top
                    sm[2*j,2*i,:]=np.asarray([2,2,1,1],dtype=int)
                    oris[2*j,2*i,:2] = np.asarray([1.0,0.0,0.0],dtype=np.float64)
                    oris[2*j,2*i,2:] = np.asarray([0.0,1.0,0.0],dtype=np.float64)
                else: #warp tow on top
                    sm[2*j,2*i,:]=np.asarray([1,1,2,2],dtype=int)
                    oris[2*j,2*i,2:] = np.asarray([1.0,0.0,0.0],dtype=np.float64)
                    oris[2*j,2*i,:2] = np.asarray([0.0,1.0,0.0],dtype=np.float64)

        #Assign tows to gap regions
        for i in range(n_warp):
            for j in range(n_weft):
                #Assign warp-warp gaps per weft tow
                if i==n_warp-1: #assumes perioidic architecture, keeps from running off array end
                    ichk=0
                else:
                    ichk=2*i+2
                if np.array_equal(sm[2*j,2*i,:],sm[2*j,ichk,:]): #adjacent warp tows in same plane
                    stack=sm[2*j,2*i,:].copy()
                    stack[stack==2]=3 #make weft tows matrix
                    sm[2*j,2*i+1,:]=stack
                    for k,v in enumerate(stack):
                        if v==1:
                            oris[2*j,2*i+1,k] = np.asarray([0.0,1.0,0.0],dtype=np.float64)
                else: #adjacent warp tows are on top/bottom
                    sm[2*j,2*i+1,:]=np.asarray([3,1,1,3],dtype=int)
                    if sm[2*j,2*i,0]==1: #2i+1 subvols have a positive angle
                        oris[2*j,2*i+1,1:]=np.asarray([0.0,1.0,tanx],dtype=np.float64)
                    else: #2i+1 subvols have a negative angle
                        oris[2*j,2*i+1,1:]=np.asarray([0.0,1.0,-tanx],dtype=np.float64)

                #Assign weft-weft gaps per warp tow
                if j==n_weft-1: #assumes perioidic architecture, keeps from running off array end
                    jchk=0
                else:
                    jchk=2*j+2
                if np.array_equal(sm[2*j,2*i,:],sm[jchk,2*i,:]): #adjacent weft tows in same plane
                    stack=sm[2*j,2*i,:].copy()
                    stack[stack==1]=3 #make warp tows matrix
                    sm[2*j+1,2*i,:]=stack
                    for k,v in enumerate(stack):
                        if v==2:
                            oris[2*j+1,2*i,k] = np.asarray([1.0,0.0,0.0],dtype=np.float64)
                else:
                    sm[2*j+1,2*i,:]=np.asarray([3,2,2,3],dtype=int)
                    if sm[2*j,2*i,0]==2: #2j+1 subvols have a positive angle
                        oris[2*j+1,2*i,1:]=np.asarray([1.0,0.0,tanx],dtype=np.float64)
                    else: #2i+1 subvols have a negative angle
                        oris[2*j+1,2*i,1:]=np.asarray([1.0,0.0,-tanx],dtype=np.float64)


        #map the plotted values (display only) to actual material numbers based on inputs
        r['sm']=np.vectorize(cv['key'].get)(sm)
        r['DIM']='3D'
        r['mod']=cv['lev0_mod']
        r['archid']=99

        #tile ruc in thickness direction
        r['sm']=np.tile(r['sm'],(1,1,cv['n']))
        oris=np.tile(oris,(1,1,cv['n'],1))
        r['na']*=cv['n']
        r['d']=np.tile(r['d'],cv['n'])


        #save crot
        #TODO: verify weave2d orientations match NASMAT built-in materials
        ori_out=[]
        for ia in range(r['na']):
            for ib in range(r['nb']):
                for ig in range(r['ng']):
                    o=oris[ig,ib,ia,:]
                    if np.any(o!=0.0):
                        ori_out.append([ia+1,ib+1,ig+1,o[2],o[1],o[0]])

        r['crot']=ori_out

        self._convert_crot(r)

        #stackify if desired
        if self.stacks_cb.isChecked():
            s=Stackify(rucs={'0':r},lev0_mod=cv['lev0_mod'],stack_mod=cv['stack_mod'],
                       nmats=self.nmats,crot=r['crot'])
            r=s.newrucs['0']
            r['child']=[]
            for key,ruc in s.newrucs.items():
                if key=='0':
                    continue
                if key in s.newcrot:
                    ruc['crot'] = s.newcrot[key]
                r['child'].append(ruc)

        self.final_ruc=r

        npp=NASMATPrePost()
        npp.set('selected',None)
        self.accept()
        self._finalize()

    def _convert_crot(self,r):
        """
        Helper function to convert crot data to arrays for later use.

        Parameters:
            r (dict): ruc parameters

        Returns:
            None.
        """
        sz=r['sm'].size
        sh=r['sm'].shape
        r['ORI_X1'] = np.zeros((sz,3),dtype=float)
        r['ORI_X2'] = np.zeros((sz,3),dtype=float)
        r['ORI_X3'] = np.zeros((sz,3),dtype=float)
        for ori in r['crot']:
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
            r['ORI_X1'][iloc]=d1
            r['ORI_X2'][iloc]=d2
            r['ORI_X3'][iloc]=d3
        r['ORI_X1_NORM']=np.sqrt(np.sum(r['ORI_X1']**2,axis=1))
        r['ORI_X2_NORM']=np.sqrt(np.sum(r['ORI_X2']**2,axis=1))
        r['ORI_X3_NORM']=np.sqrt(np.sum(r['ORI_X3']**2,axis=1))

    def cancel_2dwoven_ruc(self):
        """
        Callback function to reject 2d woven ruc.

        Parameters:
            None.

        Returns:
            None.
        """

        self.reject()
        self._finalize()

    def _finalize(self):
        """
        Callback function to finalize vtk graphics for exit.

        Parameters:
            None.

        Returns:
            None.
        """

        vtk_widget=self.findChild(QWidget, "vtk_widget")
        vtk_widget.interactor.Finalize()

    def reverse_weave(self):
        """
        Callback function to reverse 2d woven ruc.

        Parameters:
            None.

        Returns:
            None.
        """

        sm=self.ruc['sm']

        p=list(range(1,self.ruc['nb']-1,2))
        loc=np.array(np.meshgrid(p,p)).T.reshape(-1,2)
        for i in loc:
            if sm[i[0],i[1]]==1:
                sm[i[0],i[1]]=2
            elif sm[i[0],i[1]]==2:
                sm[i[0],i[1]]=1

        vtk_widget=self.findChild(QWidget, "vtk_widget")
        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        vs[id(self)]['tmp_2Dweave']=self.ruc
        npp.set('vtk_settings',vs)
        if vtk_widget:
            self._update_vtk()


    def stack_chk(self):
        """
        Callback function to set inputs for creating stacks.

        Parameters:
            None.

        Returns:
            None.
        """

        chk=self.stacks_cb.isChecked()
        self.stackmod_label.setEnabled(chk)
        self.stackmod_cb.setEnabled(chk)


    def _set_satin_weave(self,sub):
        """
        Function to set satin weave parameters.

        Parameters:
            sub (str): sub-type for weave

        Returns:
            None.
        """

        self.get_ui_vals()
        cv=self.cur_ui_vals
        d=cv['d']
        w=cv['w']
        self.ruc['type']=f"Satin-{sub}"
        if sub=='4H':
            self.ruc['na']=4
            self.ruc['d']=cv['t']/4*np.ones(self.ruc['na'])
            dims=np.tile([w,d],4)
            dims=np.insert(dims,0,d/2)
            dims[-1]=d/2
            nb=self.ruc['nb']=9
            self.ruc['h']=dims.copy()
            ng=self.ruc['ng']=9
            self.ruc['l']=dims.copy()
            if self.get_sm:
                self.ruc['sm']=np.ones([nb,ng],dtype=np.int32)*3
                self.ruc['sm'][np.ix_([1,3,5,7],[0,2,4,6,8])]=2
                self.ruc['sm'][np.ix_([0,2,4,6,8],[1,3,5,7])]=1
                self.ruc['sm'][1,1]=2
                self.ruc['sm'][1,3]=2
                self.ruc['sm'][1,5]=2
                self.ruc['sm'][1,7]=1
                self.ruc['sm'][3,1]=2
                self.ruc['sm'][3,3]=1
                self.ruc['sm'][3,5]=2
                self.ruc['sm'][3,7]=2
                self.ruc['sm'][5,1]=2
                self.ruc['sm'][5,3]=2
                self.ruc['sm'][5,5]=1
                self.ruc['sm'][5,7]=2
                self.ruc['sm'][7,1]=1
                self.ruc['sm'][7,3]=2
                self.ruc['sm'][7,5]=2
                self.ruc['sm'][7,7]=2
                self.ruc['pickable']=np.zeros([nb,ng],dtype=np.int32)
                p=[1,3,5,7]
                loc=np.array(np.meshgrid(p,p)).T.reshape(-1,2)
                for i in loc:
                    self.ruc['pickable'][i[0],i[1]]=1
        elif sub=='5H':
            self.ruc['na']=4
            self.ruc['d']=cv['t']/4*np.ones(self.ruc['na'])
            dims=np.tile([w,d],5)
            dims=np.insert(dims,0,d/2)
            dims[-1]=d/2
            nb=self.ruc['nb']=11
            self.ruc['h']=dims.copy()
            ng=self.ruc['ng']=11
            self.ruc['l']=dims.copy()
            if self.get_sm:
                self.ruc['sm']=np.ones([nb,ng],dtype=np.int32)*3
                self.ruc['sm'][np.ix_([1,3,5,7,9],[0,2,4,6,8,10])]=2
                self.ruc['sm'][np.ix_([0,2,4,6,8,10],[1,3,5,7,9])]=1
                self.ruc['sm'][1,1]=2
                self.ruc['sm'][1,3]=2
                self.ruc['sm'][1,5]=1
                self.ruc['sm'][1,7]=2
                self.ruc['sm'][1,9]=2
                self.ruc['sm'][3,1]=2
                self.ruc['sm'][3,3]=2
                self.ruc['sm'][3,5]=2
                self.ruc['sm'][3,7]=2
                self.ruc['sm'][3,9]=1
                self.ruc['sm'][5,1]=2
                self.ruc['sm'][5,3]=1
                self.ruc['sm'][5,5]=2
                self.ruc['sm'][5,7]=2
                self.ruc['sm'][5,9]=2
                self.ruc['sm'][7,1]=2
                self.ruc['sm'][7,3]=2
                self.ruc['sm'][7,5]=2
                self.ruc['sm'][7,7]=1
                self.ruc['sm'][7,9]=2
                self.ruc['sm'][9,1]=1
                self.ruc['sm'][9,3]=2
                self.ruc['sm'][9,5]=2
                self.ruc['sm'][9,7]=2
                self.ruc['sm'][9,9]=2
                self.ruc['pickable']=np.zeros([nb,ng],dtype=np.int32)
                p=[1,3,5,7,9]
                loc=np.array(np.meshgrid(p,p)).T.reshape(-1,2)
                for i in loc:
                    self.ruc['pickable'][i[0],i[1]]=1
        elif sub=='8H':
            self.ruc['na']=4
            self.ruc['d']=cv['t']/4*np.ones(self.ruc['na'])
            dims=np.tile([w,d],8)
            dims=np.insert(dims,0,d/2)
            dims[-1]=d/2
            nb=self.ruc['nb']=17
            self.ruc['h']=dims.copy()
            ng=self.ruc['ng']=17
            self.ruc['l']=dims.copy()
            if self.get_sm:
                self.ruc['sm']=np.ones([nb,ng],dtype=np.int32)*3
                olist=list(range(1,17,2))
                elist=list(range(0,17,2))
                self.ruc['sm'][np.ix_(olist,elist)]=2
                self.ruc['sm'][np.ix_(elist,olist)]=1
                self.ruc['sm'][np.ix_(olist,olist)]=2
                plist=[15,9,3,13,7,1,11,5]
                for i,o in enumerate(olist):
                    self.ruc['sm'][plist[i],o]=1

                self.ruc['pickable']=np.zeros([nb,ng],dtype=np.int32)
                p=olist
                loc=np.array(np.meshgrid(p,p)).T.reshape(-1,2)
                for i in loc:
                    self.ruc['pickable'][i[0],i[1]]=1

    def _set_basket_weave(self,sub):
        """
        Function to set basket weave parameters.

        Parameters:
            sub (str): sub-type for weave

        Returns:
            None.
        """

        self.get_ui_vals()
        cv=self.cur_ui_vals
        d=cv['d']
        w=cv['w']
        self.ruc['type']=f"Basket-{sub}"

        runitb=int(sub.split('x')[0])
        runitg=int(sub.split('x')[1])
        self.ruc['na']=4
        self.ruc['d']=cv['t']/4*np.ones(self.ruc['na'])

        nb=self.ruc['nb']=4*runitb+1
        ng=self.ruc['ng']=4*runitg+1
        dims=np.tile([w,d],2*runitb)
        dims=np.insert(dims,0,d/2)
        dims[-1]=d/2
        self.ruc['h']=dims.copy()
        dims=np.tile([w,d],2*runitg)
        dims=np.insert(dims,0,d/2)
        dims[-1]=d/2
        self.ruc['l']=dims.copy()

        if self.get_sm:
            self.ruc['sm']=np.ones([nb,ng],dtype=np.int32)*3
            olistb=list(range(1,nb,2))
            olistg=list(range(1,ng,2))
            elistb=list(range(0,nb,2))
            elistg=list(range(0,ng,2))
            self.ruc['sm'][np.ix_(olistb,elistg)]=2
            self.ruc['sm'][np.ix_(elistb,olistg)]=1
            self.ruc['sm'][np.ix_(olistb,olistg)]=1
            for i in range(2):
                olist=list(range(1+2*i*runitb,2*runitg+2*i*runitb,2))
                self.ruc['sm'][np.ix_(olist,olist)]=2

            self.ruc['pickable']=np.zeros([nb,ng],dtype=np.int32)
            olist=list(range(1,nb,2))
            elist=list(range(1,ng,2))
            self.ruc['pickable'][np.ix_(olist,elist)]=1


    def _set_user_weave(self):
        """
        Function to set user weave parameters.

        Parameters:
            None.

        Returns:
            None.
        """

        self.get_ui_vals()
        cv=self.cur_ui_vals
        d=cv['d']
        w=cv['w']
        self.ruc['type']='User'
        self.ruc['na']=4
        self.ruc['d']=cv['t']/4*np.ones(self.ruc['na'])

        dims=np.tile([w,d],cv['n_warp'])
        dims=np.insert(dims,0,d/2)
        dims[-1]=d/2
        nb=self.ruc['nb']=len(dims)
        self.ruc['h']=dims.copy()
        dims=np.tile([w,d],cv['n_weft'])
        dims=np.insert(dims,0,d/2)
        dims[-1]=d/2
        ng=self.ruc['ng']=len(dims)
        self.ruc['l']=dims.copy()
        if self.get_sm:
            self.ruc['sm']=np.ones([nb,ng],dtype=np.int32)*3
            olistb=list(range(1,nb,2))
            olistg=list(range(1,ng,2))
            elistb=list(range(0,nb,2))
            elistg=list(range(0,ng,2))
            self.ruc['sm'][np.ix_(olistb,elistg)]=2
            self.ruc['sm'][np.ix_(elistb,olistg)]=1
            self.ruc['sm'][np.ix_(olistb,olistg)]=2
            self.ruc['pickable']=np.zeros([nb,ng],dtype=np.int32)
            olist=list(range(1,nb,2))
            elist=list(range(1,ng,2))
            self.ruc['pickable'][np.ix_(olist,elist)]=1

    def _set_twill_weave(self,sub):
        """
        Function to set twill weave parameters.

        Parameters:
            sub (str): sub-type for weave

        Returns:
            None.
        """

        self.get_ui_vals()
        cv=self.cur_ui_vals
        d=cv['d']
        w=cv['w']
        self.ruc['type']=f"Twill-{sub}"
        if sub=='2x2':
            self.ruc['na']=4
            self.ruc['d']=cv['t']/4*np.ones(self.ruc['na'])
            dims=np.tile([w,d],4)
            dims=np.insert(dims,0,d/2)
            dims[-1]=d/2
            nb=self.ruc['nb']=9
            self.ruc['h']=dims.copy()
            ng=self.ruc['ng']=9
            self.ruc['l']=dims.copy()
            if self.get_sm:
                self.ruc['sm']=np.ones([nb,ng],dtype=np.int32)*3
                self.ruc['sm'][np.ix_([1,3,5,7],[0,2,4,6,8])]=2
                self.ruc['sm'][np.ix_([0,2,4,6,8],[1,3,5,7])]=1
                self.ruc['sm'][1,1]=2
                self.ruc['sm'][1,3]=2
                self.ruc['sm'][1,5]=1
                self.ruc['sm'][1,7]=1
                self.ruc['sm'][3,1]=2
                self.ruc['sm'][3,3]=1
                self.ruc['sm'][3,5]=1
                self.ruc['sm'][3,7]=2
                self.ruc['sm'][5,1]=1
                self.ruc['sm'][5,3]=1
                self.ruc['sm'][5,5]=2
                self.ruc['sm'][5,7]=2
                self.ruc['sm'][7,1]=1
                self.ruc['sm'][7,3]=2
                self.ruc['sm'][7,5]=2
                self.ruc['sm'][7,7]=1
                self.ruc['pickable']=np.zeros([nb,ng],dtype=np.int32)
                p=[1,3,5,7]
                loc=np.array(np.meshgrid(p,p)).T.reshape(-1,2)
                for i in loc:
                    self.ruc['pickable'][i[0],i[1]]=1

    def _set_plain_weave(self):
        """
        Function to set plain weave parameters.

        Parameters:
            None.

        Returns:
            None.
        """

        self.get_ui_vals()
        cv=self.cur_ui_vals
        d=cv['d']
        w=cv['w']

        self.ruc['type']='Plain'
        self.ruc['na']=4
        self.ruc['d']=cv['t']/4*np.ones(self.ruc['na'])
        dims=np.tile([w,d],2)
        dims=np.insert(dims,0,d/2)
        dims[-1]=d/2
        nb=self.ruc['nb']=5
        self.ruc['h']=dims.copy()
        ng=self.ruc['ng']=5
        self.ruc['l']=dims.copy()

        #initialize 2D SM array with default matrix = 3
        if self.get_sm:
            self.ruc['sm']=np.ones([nb,ng],dtype=np.int32)*3
            self.ruc['sm'][np.ix_([1,3],[0,2,4])]=2
            self.ruc['sm'][1,1]=2
            self.ruc['sm'][3,3]=2
            self.ruc['sm'][np.ix_([0,2,4],[1,3])]=1
            self.ruc['sm'][3,1]=1
            self.ruc['sm'][1,3]=1
            self.ruc['pickable']=np.zeros([nb,ng],dtype=np.int32)
            self.ruc['pickable'][np.ix_([1,3],[1,3])]=1

    def _tile_weave_in_plane(self):
        """
        Function to tile 2d weave in-plane.

        Parameters:
            None.

        Returns:
            None.
        """
        self.get_ui_vals()
        cv=self.cur_ui_vals

        warp_repeats=cv['warp_repeats']
        weft_repeats=cv['weft_repeats']

        ruc=self.base_ruc

        self.ruc['h']=self._tile_1d(ruc['h'],weft_repeats)
        self.ruc['l']=self._tile_1d(ruc['l'],warp_repeats)
        self.ruc['sm']=self._tile_2d(ruc['sm'],warp_repeats,weft_repeats)
        self.ruc['pickable']=self._tile_2d(ruc['pickable'],warp_repeats,weft_repeats)
        self.ruc['nb'],self.ruc['ng']=self.ruc['sm'].shape

    def _tile_1d(self,array,nrep):
        """
        Function to tile a 1d array.

        Parameters:
            array (np.ndarray): input array
            nrep (int): number of repeats for tiling

        Returns:
            newarray (np.ndarray): updated array
        """

        if nrep==1:
            return array

        core=array[1:-1]
        h=array[0]
        newarray=np.zeros(nrep*len(core)+nrep+1,dtype=float)
        newarray[0]=h
        for i in range(nrep):
            st=1+i*(len(core)+1)
            newarray[st:st+len(core)]=core
            if i>0:
                newarray[st-1]=2*h
        newarray[-1]=h

        return newarray


    def _tile_2d(self,array,xrep,yrep):
        """
        Function to tile a 2d array.

        Parameters:
            array (np.ndarray): input array
            xrep (int): number of x repeats for tiling
            yrep (int): number of y repeats for tiling

        Returns:
            newarray (np.ndarray): updated array
        """

        core=array[:-1,:-1]
        last_row=array[-1,:-1]
        last_col=array[:-1,-1]
        corner = array[-1,-1]

        m,n=core.shape

        newarray = np.zeros((yrep*m+1,xrep*n+1),dtype=int)
        for i in range(yrep):
            for j in range(xrep):
                newarray[i*m:(i+1)*m,j*n:(j+1)*n]+=core

        for i in range(yrep):
            newarray[i*m:(i+1)*m,-1]+=last_col

        for j in range(xrep):
            newarray[-1,j*n:(j+1)*n]+=last_row

        newarray[-1,-1]+=corner

        return newarray


    def get_ui_vals(self):
        """
        Function to get UI parameters.

        Parameters:
            None.

        Returns:
            None.
        """

        cv=self.cur_ui_vals

        try:
            cv['t']=float(self.woven_plythk.text())
        except (ValueError, TypeError):
            print('invalid input for ply thickness in 2D WeaveMaker, resetting...')
            cv['t']=0.2
            self.woven_plythk.setText('0.2')

        try:
            cv['d']=float(self.woven_tow_spacing.text())
        except (ValueError, TypeError):
            print('invalid input for tow spacing in 2D WeaveMaker, resetting...')
            cv['d']=0.2
            self.woven_tow_spacing.setText('0.2')

        try:
            cv['w']=float(self.woven_tow_width.text())
        except (ValueError, TypeError):
            print('invalid input for tow width in 2D WeaveMaker, resetting...')
            cv['w']=0.8
            self.woven_tow_width.setText('0.8')

        try:
            cv['n']=int(self.woven_nplies.text())
            self.woven_nplies.setText(str(cv['n']))
        except (ValueError, TypeError):
            print('invalid input for no. of plies in 2D WeaveMaker, resetting...')
            cv['n']=1
            self.woven_nplies.setText('1')

        try:
            cv['n_warp']=int(self.nwarp_tows.text())
            self.nwarp_tows.setText(str(cv['n_warp']))
        except (ValueError, TypeError):
            print('invalid input for no. of warp tows in 2D WeaveMaker, resetting...')
            cv['n_warp']=2
            self.nwarp_tows.setText('2')

        try:
            cv['n_weft']=int(self.nweft_tows.text())
            self.nweft_tows.setText(str(cv['n_weft']))
        except (ValueError, TypeError):
            print('invalid input for no. of weft tows in 2D WeaveMaker, resetting...')
            cv['n_weft']=2
            self.nweft_tows.setText('2')

        try:
            cv['warp_repeats']=int(self.warp_repeats.text())
            self.warp_repeats.setText(str(cv['warp_repeats']))
        except (ValueError, TypeError):
            print('invalid input for no. of warp repeats in 2D WeaveMaker, resetting...')
            cv['warp_repeats']=1
            self.warp_repeats.setText('1')

        try:
            cv['weft_repeats']=int(self.weft_repeats.text())
            self.weft_repeats.setText(str(cv['weft_repeats']))
        except (ValueError, TypeError):
            print('invalid input for no. of weft repeats in 2D WeaveMaker, resetting...')
            cv['weft_repeats']=1
            self.weft_repeats.setText('1')

        cv['warp']=int(self.woven_warp_mat.currentText())
        cv['weft']=int(self.woven_weft_mat.currentText())
        cv['matrix']=int(self.woven_Mmat.currentText())
        cv['lev0_mod']=int(self.lev0mod_cb.currentText().replace(' ','').split('-')[0])
        cv['stack_mod']=int(self.stackmod_cb.currentText().replace(' ','').split('-')[0])

        cv['key']={1:cv['weft'],2:cv['warp'],3:cv['matrix']}


    def update_user_weave(self):
        """
        Callback function to update 2d weave.

        Parameters:
            None.

        Returns:
            None.
        """

        self.last_weave+='-old'
        self.set_2dwoven_sub()


    def get_2dwoven_subcb(self):
        """
        Callback function to update specific options for a 2d weave type.

        Parameters:
            None.

        Returns:
            None.
        """

        if self.subcb_set:
            self.set_2dwoven_sub(sub_update=False)

    def set_2dwoven_geom(self):
        """
        Callback function to set 2d weave geometry.

        Parameters:
            None.

        Returns:
            None.
        """
        self.get_sm=False
        self.set_2dwoven_sub()

    def set_2dwoven_sub(self,sub_update=True):
        """
        Callback function to set 2d weave type.

        Parameters:
            sub_update (bool): flag to update UI

        Returns:
            None.
        """

        weave=self.woven2d_cb.currentText()
        if weave=='Plain':
            self.woven2dsub_cb.clear()
            self.woven2dsub_cb.setEnabled(False)

        if sub_update:
            self.subcb_set=False
            self.woven2dsub_cb.clear()
            self.woven2dsub_cb.setEnabled(True)
            if weave=='Twill':
                self.woven2dsub_cb.addItems(['2x2'])
                self.subcb_set=True
            elif weave=='Satin':
                self.woven2dsub_cb.addItems(['4H','5H','8H'])
                self.subcb_set=True
            elif weave=='Basket':
                self.woven2dsub_cb.addItems(['2x2','3x3','4x4','5x5'])
                self.subcb_set=True
            else:
                self.woven2dsub_cb.setEnabled(False)

        self.nwarp_tows.setEnabled(False)
        self.nweft_tows.setEnabled(False)
        sub=self.woven2dsub_cb.currentText()
        if sub:
            weave=weave+f"-{sub}"

        if weave!=self.last_weave:
            self.ruc={}
            self.last_weave=weave
            self.get_sm=True


        if weave.startswith('Plain'):
            self._set_plain_weave()
        elif weave.startswith('Twill'):
            self._set_twill_weave(sub)
        elif weave.startswith('Satin'):
            self._set_satin_weave(sub)
        elif weave.startswith('Basket'):
            self._set_basket_weave(sub)
        elif weave.startswith('User'):
            self.nwarp_tows.setEnabled(True)
            self.nweft_tows.setEnabled(True)
            self._set_user_weave()

        self.base_ruc=self.ruc.copy()

        vtk_widget=self.findChild(QWidget, "vtk_widget")
        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        vs[id(self)]['tmp_2Dweave']=self.ruc
        # vs[id(self)]['show_mats']=True #enable to show id numbers for plot checking
        npp.set('vtk_settings',vs)
        if vtk_widget:
            self._update_vtk()


    def tile_ruc(self):
        """
        Callback function to tile 2d weave.

        Parameters:
            None.

        Returns:
            None.
        """

        self._tile_weave_in_plane()
        vtk_widget=self.findChild(QWidget, "vtk_widget")
        if vtk_widget:
            self._update_vtk()


#-----------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    app = QApplication([])
    widget = woven2d_Dialog(mats=['1','2'])
    widget.show()
    exit_code = app.exec_()
    sys.exit(exit_code)
