'''Example 3: Modifying a NASMAT input deck that utilizes parameters, updates
              parameters, runs NASMAT, and processes results.
''' #pylint: disable=C0103
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from util.npp_settings import get_npp_settings #pylint: disable=C0413
from util.sub_param import SubParam #pylint: disable=C0413
from util.output_parser import output_parser #pylint: disable=C0413
from NASMAT import NASMAT #pylint: disable=C0413


#truncated normal function for varying parameters
def truncated_normal(mean,cv,size,rng):
    """
    Returns random numbers associated with a truncated normal distribution.
    No values less than 0 are allowed (can result in aphysical behavior)

    Parameters:
        mean (float): mean value for the distribution
        cv (float): coefficient of variation for the distribution
        size (int): number of values to return
        rng (np.random.Generator): random number generator

    Returns:
        None.
    """

    std = mean*cv
    samples = rng.normal(mean, std, size)
    while np.any(samples < 0):
        mask = samples < 0
        samples[mask] = rng.normal(mean, std, mask.sum())
    return samples


#Define NASMAT input deck filename and location
INFILE='HF2D_MSRM_w_params.MAC'
NJOBS = 50
RUN_NASMAT = True

rgen = np.random.default_rng(123456) #seed for random generator so results are repeatable
E_M  = truncated_normal(mean=4670.0,cv=0.1,size=NJOBS,rng=rgen) #matrix modulus
vf_F = truncated_normal(mean=0.55,cv=0.1,size=NJOBS,rng=rgen) #fiber volume fraction
vf_V = truncated_normal(mean=0.05,cv=0.01,size=NJOBS,rng=rgen) #void void fraction
Xn_M = truncated_normal(mean=59.4,cv=0.2,size=NJOBS,rng=rgen) #matrix tensile strength

##################################################################################################
# Get existing NASMAT environment. See README for details on setting variables
npps = get_npp_settings(echo=True)

wdir=os.path.join(os.getcwd(),'standalone_examples')
macfile=os.path.join(wdir,INFILE)

#Create NASMAT jobs by performing parameter substitutions
macjobs = []
for i,(E_M_i, vf_F_i, vf_V_i, Xn_M_i) in enumerate(zip(E_M, vf_F, vf_V, Xn_M)):
    #update default values, keys must match parameters in macfile
    update_param = {'E_M':E_M_i, 'vf_F':vf_F_i, 'vf_V':vf_V_i,
                    'Xn_M':Xn_M_i,'macro_name':i}
    macjobs.append(macfile[:-4]+f"_{i}.MAC")
    #substitute and create ids
    SubParam(param_mac=macfile,update_param=update_param,workdir=wdir,fileid=i)

# Run NASMAT
if RUN_NASMAT:
    for job in macjobs:
        nasmat=NASMAT(npps['NASMAT_SOLVER'],npps['HDF5_PATH'],npps['INTEL_PATH'],npps['INTEL_OPTS'])
        nasmat.run(mac=job)

#Get output data for plotting
outdata = {'E22':np.zeros(NJOBS),'S22':np.zeros(NJOBS)}
#Parse output file and extract effective properties
macout = [file[:-4]+'.out' for file in macjobs]
for i,file in enumerate(macout):
    d = output_parser(fname=file)
    outdata['E22'][i] = d['E22S']

#Parse *.data files
for i,file in enumerate(macout):
    directory, filename = os.path.split(file)
    base, _ = os.path.splitext(filename)

    data_file = os.path.join(directory, base.upper()+'_macro.data')
    d = np.loadtxt(data_file)

    outdata['S22'][i] = d[:,1].max()
    max_ind = d[:,1].argmax()
    if max_ind == d.shape[0] - 1:
        print(f"Warning: maximum value occurs at last index of data in {data_file}.")


#convert data to array for plotting
for key,val in outdata.items():
    outdata[key]=np.asarray(val)


# Create 2x2 subplot figure
data = [(E_M, outdata['E22']), (vf_V, outdata['E22']),
        (vf_F, outdata['S22']), (Xn_M, outdata['S22'])]

xlabels = ['Matrix Modulus (MPa)', 'Void Volume Fraction (-)',
           'Fiber Volume Fraction (-)', 'Matrix Tensile Strength (MPa)']
ylabels = ['RUC 2-dir Stiffness (MPa)', 'RUC 2-dir Stiffness (MPa)',
            'RUC 2-dir Strength (MPa)','RUC 2-dir Strength (MPa)']

fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes = axes.flatten()
for ax,(x, y),xlabel,ylabel in zip(axes, data, xlabels,ylabels):
    ax.scatter(x, y)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

plt.tight_layout()
plt.show()
