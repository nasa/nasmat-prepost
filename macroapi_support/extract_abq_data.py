"""
The following code generates a Python script that is executed
from Abaqus (command line or CAE). It extracts a set of user
inputs from an existing Abaqus ODB file and stores the data
in a NumPy file (*.npy).

Modifications are required if more complex steps or loading
conditions are utilized. The code assumes that the requested
variables are available.

View the README.md file in the main project directory for more
instructions on use.
"""
from abaqus import * #pylint: disable=E0401,W0401
from abaqusConstants import * #pylint: disable=E0401,W0401
from caeModules import * #pylint: disable=E0401,W0401
from odbAccess import * #pylint: disable=E0401,W0401
import numpy as np


FNAME = 'AbqTest1.odb' #existing Abaqus ODB file
STEP_NAME='Step-1' #available step name
INST_NAME='PART-1-1' #available instance name
ALL_SET_NAME='ALLELEMS' #defined set name that contains all elements in the model as
                        #defined in the ODB (file may have a different case)
field_out=['S','E'] #field output names
N_SDVS = 21 #number of state variables to be added
hist_out=['COORD1','COORD2','COORD3'] #history output names

###################################################################################################
#append state variables to history output
hist_out = hist_out + [f"SDV{i+1}" for i in range(N_SDVS)]

#open the odb and get the frames for a defined step
odb = openOdb(path=FNAME) #pylint: disable=E0602
myAssembly = odb.rootAssembly
print('available steps:', odb.steps.keys())
frameRepository = odb.steps[STEP_NAME].frames

#get dimensions to allocate data arrays
max_inc=int(frameRepository[-1].description.split(':')[0].split('Increment')[1].strip())+1
elems=odb.rootAssembly.instances[INST_NAME].elementSets[ALL_SET_NAME].elements
elem_labels=np.array([elem.label for elem in elems],dtype=int)
n_elems=len(elems)
d=frameRepository[-1].fieldOutputs[field_out[0]]
max_ip=max(len(d.getSubset(position=INTEGRATION_POINT,region=elem).values) for elem in elems) #pylint: disable=E0602
tensor_len=[len(frameRepository[-1].fieldOutputs[v].componentLabels) for v in field_out]
max_tensor = int(sum(len(frameRepository[-1].fieldOutputs[v].componentLabels) for v in field_out))

all_field_data=np.zeros(shape=(max_inc,n_elems,max_ip,max_tensor),dtype=float)
all_hist_data=np.zeros(shape=(max_inc,n_elems,max_ip,len(hist_out)),dtype=float)


#loop through frames to get requested field data
for frame in frameRepository:
    inc=int(frame.description.split(':')[0].split('Increment')[1].strip())
    IC=0
    for v, var in enumerate(field_out):
        D = frame.fieldOutputs[var]
        trng = [IC, tensor_len[v] + IC]
        IC = tensor_len[v] + IC

        for e in range(n_elems):
            elem=elems[e]
            d=D.getSubset(position=INTEGRATION_POINT,region=elem) #pylint: disable=E0602
            vals=d.values
            for val, v in enumerate(vals):
                all_field_data[inc, e, val, trng[0]:trng[1]] = np.array(v.data)


#loop through frames to get requested history data
hist=odb.steps[STEP_NAME].historyRegions
all_keys=[key for key in hist.keys() if key.startswith('Element')]
for key in all_keys:
    h=hist[key]
    #keys look like - 'Element DOGBONE-1.160 Int Point 8'
    eip=key.split(f"Element {INST_NAME}.")[1].split(' ')
    e=np.where(elem_labels==int(eip[0]))[0]
    ip=int(eip[-1])-1
    for v, hname in enumerate(hist_out):
        hd = h.historyOutputs[hname]
        for inc, hdata in enumerate(hd.data):
            all_hist_data[inc, e, ip, v] = hdata[1]


#save the data to a NPY file
with open(FNAME[:-4]+'.npy', 'wb') as f:
    np.save(f, elem_labels,allow_pickle=False)
    np.save(f,np.array(field_out),allow_pickle=False)
    np.save(f,np.array(tensor_len),allow_pickle=False)
    np.save(f,np.array(hist_out),allow_pickle=False)
    np.save(f, all_field_data,allow_pickle=False)
    np.save(f, all_hist_data,allow_pickle=False)
