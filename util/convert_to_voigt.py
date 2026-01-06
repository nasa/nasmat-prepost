""" function to convert between 2nd order tensor and Voight notation"""
import numpy as np

def convert_to_voigt(array,eng_shear=True):
    """
    converts 2nd order tensor notation to Voight notation

    Parameters:
        array (np.ndarray): input array in 2nd order tensor notation
        eng_shear (bool): flag to convert shear terms

    Returns:
        voigt_array (np.ndarray): output voight notation
    """

    if eng_shear: #convert engineering to tensorial shear quantities
        factor=2.0
    else:
        factor=1.0

    n_cells = array.shape[0]
    voigt_array = np.zeros((n_cells, 6))
    voigt_array[:, 0] = array[:, 0, 0]  #11
    voigt_array[:, 1] = array[:, 1, 1]  #22
    voigt_array[:, 2] = array[:, 2, 2]  #33
    voigt_array[:, 3] = array[:, 1, 2]*factor  #23
    voigt_array[:, 4] = array[:, 0, 2]*factor  #13
    voigt_array[:, 5] = array[:, 0, 1]*factor  #12
    return voigt_array
