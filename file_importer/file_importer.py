"""Importer for reading and converted external files into NASMAT"""
import numpy as np
#from vtkmodules.vtkIOXML import vtkXMLImageDataReader # pylint: disable=E0611
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader # pylint: disable=E0611
from vtkmodules.vtkCommonDataModel import vtkCellLocator # pylint: disable=E0611
from vtkmodules.vtkCommonCore import vtkIdList # pylint: disable=E0611
from vtk.util.numpy_support import vtk_to_numpy # pylint: disable=E0611,E0401

#TODO: add FileImporter support to UI
class FileImporter(): #pylint: disable=R0902
    """Reads an input file type and converts the geometry into NASMAT's format"""
    def __init__(self,filename,array_mapping,scale_dim=1.0,search_tolerance=0.0001):
        """
        Initializes class.
        """

        self.file_type=filename.lower().rsplit('.', 1)[-1]
        if self.file_type=='vtu':
            file=vtkXMLUnstructuredGridReader()
            file.SetFileName(filename)
            file.Update()
            self.input=file.GetOutput()
            print(f"Number of Cells: {self.input.GetNumberOfCells()}")
        elif self.file_type=='vti':
            #TODO: add vti file support for FileImporter
            raise NotImplementedError('VTI input file type not supported')
        #     file=vtkXMLImageDataReader()
        #     file.SetFileName(filename)
        #     file.Update()
        #     self.input=file.GetOutput()
        #     print('Number of Cells: %d'%self.input.GetNumberOfCells())
        #     print('Dimensions: ',self.input.GetDimensions())
        #     print('Extents: ',self.input.GetExtent())
        #     print('Bounds: ',self.input.GetBounds())

        self.filename=filename
        self.tol=search_tolerance
        self.array_mapping=array_mapping
        self.scale_dim=scale_dim
        self.update_mats={}
        self.ruc=None

    def perform_conversion(self):
        """
        function to convert input model to NASMAT
    
        Parameters:
            None.
    
        Returns:
            None.
        """
        if self.update_mats:
            self._update_mats_in_sm()
        self._get_ruc()


    def _get_ruc(self):
        """
        function to determine RUC from input
    
        Parameters:
            None.
    
        Returns:
            None.
        """

        if self.file_type=='vti':
            [nb,ng,na]=self.input.GetDimensions() #based on points, not cells so subract 1
            na-=1
            nb-=1
            ng-=1
            [h,l,d]=self.input.GetSpacing()
        elif self.file_type=='vtu':
            bounds=self.input.GetBounds()
            #Create cell locator
            cloc=vtkCellLocator()
            cloc.SetDataSet(self.input)
            cloc.BuildLocator()

            pts=[bounds[0]-1,bounds[1]+1,bounds[2]-1, \
                 bounds[3]+1,bounds[4]-1,bounds[5]+1]

            xcells=vtkIdList()
            ycells=vtkIdList()
            zcells=vtkIdList()
            # print('bounds: ', bounds)
            cloc.FindCellsAlongLine([pts[0],bounds[2],bounds[4]],[pts[1],bounds[2],bounds[4]],
                                    self.tol,xcells)
            # print('xloc: ', [pts[0],bounds[2],bounds[4]],[pts[1],bounds[2],bounds[4]])
            nx=xcells.GetNumberOfIds()
            cloc.FindCellsAlongLine([bounds[0],pts[2],bounds[4]],[bounds[0],pts[3],bounds[4]],
                                    self.tol,ycells)
            # print('yloc: ', [bounds[0],pts[2],bounds[4]],[bounds[0],pts[3],bounds[4]])
            ny=ycells.GetNumberOfIds()
            cloc.FindCellsAlongLine([bounds[0],bounds[2],pts[4]],[bounds[0],bounds[2],pts[5]],
                                    self.tol,zcells)
            # print('zloc: ', [bounds[0],bounds[2],pts[4]],[bounds[0],bounds[2],pts[5]])
            nz=zcells.GetNumberOfIds()

            nb=nx
            ng=ny
            na=nz


        ruc={}
        ruc['nrucs']=1
        ruc0={}
        ruc0['msm']=0
        ruc0['na']=na
        ruc0['nb']=nb
        ruc0['ng']=ng
        ruc0['archid']=99
        ruc0['DIM']='3D'

        if self.file_type=='vti':
            ruc0['d']=np.array([d for a in range(na)],dtype=np.double)
            ruc0['h']=np.array([h for b in range(nb)],dtype=np.double)
            ruc0['l']=np.array([l for g in range(ng)],dtype=np.double)

        elif self.file_type=='vtu':
            ruc0['h']=np.array([(bounds[1]-bounds[0])/nx \
                              for a in range(nx)],dtype=np.double)
            ruc0['l']=np.array([(bounds[3]-bounds[2])/ny \
                              for b in range(ny)],dtype=np.double)
            ruc0['d']=np.array([(bounds[5]-bounds[4])/nz \
                              for g in range(nz)],dtype=np.double)

        ruc0['d']*=self.scale_dim
        ruc0['h']*=self.scale_dim
        ruc0['l']*=self.scale_dim

        sm=self.input.GetCellData().GetArray(self.array_mapping['mat'])
        sms=[sm.GetComponent(cell,0) for cell in range(self.input.GetNumberOfCells())]

        ruc0['sm']=np.array(sms,dtype=int).reshape((nb,ng,na),order='F')
        ruc0['sm']=np.swapaxes(ruc0['sm'],0,1)

        if 'ori' in self.array_mapping.keys(): #create orientation inputs for NASMAT
            ori=self.input.GetCellData().GetArray(self.array_mapping['ori'])
            oris=[[ori.GetComponent(cell,0),ori.GetComponent(cell,1),ori.GetComponent(cell,2)]
                    for cell in range(self.input.GetNumberOfCells())]
            oris=np.array(oris,dtype=np.float64).reshape((nb,ng,na,3),order='F')
            oris=np.swapaxes(oris,0,1)

            ori_out=[]
            for ia in range(ruc0['na']):
                for ib in range(ruc0['nb']):
                    for ig in range(ruc0['ng']):
                        o=oris[ig,ib,ia,:]
                        if np.any(o!=0.0):
                            ori_out.append([ia+1,ib+1,ig+1,o[2],o[0],o[1]])

            ruc['crot']={'0':ori_out}

        ruc['rucs']={'0':ruc0}
        self.ruc=ruc
        print('model successfully converted to NASMAT...')

    def get_mats(self):
        """
        function to get unique material numbers
    
        Parameters:
            None.
    
        Returns:
            None.
        """

        sm=self.input.GetCellData().GetArray(self.array_mapping['mat'])
        return np.unique(vtk_to_numpy(sm))

    def set_update_mats(self,update_mats):
        """
        function to set updated material numbers 
    
        Parameters:
            update_mats (dict): mapping used to update material numbers
    
        Returns:
            None.
        """

        self.update_mats=update_mats

    def _update_mats_in_sm(self):
        """
        function to update material numbers in materail number array
    
        Parameters:
            None.
    
        Returns:
            None.
        """

        sm=self.input.GetCellData().GetArray(self.array_mapping['mat'])
        for i in range(self.input.GetNumberOfCells()):
            val=str(int(sm.GetValue(i)))
            if val in self.update_mats.keys():
                sm.SetValue(i,self.update_mats[val])
        print('updated material numbers in RUC...')
