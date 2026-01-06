"""
Support utility for adding Abaqus data stored in a NumPy file
(*.npy) to an existing Abaqus-generated NASMAT h5 file.

Modification may be required depending on the
`extract_abq_data.py` setup.

See the README.md file in the main project directory for more
instructions on use.
"""
import numpy as np
import h5py

#Define the filename for the *.npy file containing previously extracted Abaqus data
FNAME = 'AbqTest1.npy'
###################################################################################################
#open and read arrays in. must be defined in the same order as in extract_abq_data.py
with open(FNAME, 'rb') as f:
    elem_labels=np.load(f)
    field_out=np.load(f)
    tensor_len=np.load(f)
    hist_out=np.load(f)
    all_field_data = np.load(f)
    all_hist_data = np.load(f)

#compute number of increments from data
n_inc=all_field_data.shape[0]

#open NASMAT h5 file and write data
H5NAME=FNAME[:-4]+'.h5'
with h5py.File(H5NAME, "r+") as h5:
    coords=all_hist_data[0,:,:,0:3].reshape(-1,3) #only first increment needed [first index]
    if 'Integration Point Coords' in h5['MACROAPI MESH']:
        del h5['MACROAPI MESH']['Integration Point Coords']
    h5['MACROAPI MESH'].create_dataset('Integration Point Coords',data=coords)

    if 'MACROAPI RESULTS' in h5:
        res=h5['MACROAPI RESULTS']
    else:
        res=h5.create_group('MACROAPI RESULTS')

    for i in range(n_inc):
        ISTR=f"Inc={i}"

        if ISTR in res:
            inc=res[ISTR]
        else:
            inc=res.create_group(f"Inc={i}")

        IC=0
        for v,var in enumerate(field_out):
            trng=[IC,tensor_len[v]+IC]
            d=all_field_data[i,:,:,trng[0]:trng[1]].reshape(-1,tensor_len[v])
            d[:, [-2, -1]] = d[:, [-1, -2]] #swap order of last two columns
            if var in inc:
                del inc[var]
            inc.create_dataset(var,data=d)
            IC=tensor_len[v]+IC

        #store state variables (assuming 6)
        sv=all_hist_data[i,:,:,3:].reshape(-1,6)

        if 'State Variables' in inc:
            del inc['State Variables']

        inc.create_dataset('State Variables',data=sv)
