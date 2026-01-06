""" function to convert between Voight and 2nd order tensor notation"""
import numpy as np

def convert_to_2nd_order_tensor(array,eng_shear=True):
    """
    converts Voight notation to 2nd order tensor notation

    Parameters:
        array (np.ndarray): input array in voight notation
        eng_shear (bool): flag to convert shear terms

    Returns:
        tensor2 (np.ndarray): output 2nd order tensor array
    """

    if eng_shear: #convert engineering to tensorial shear quantities
        factor=2.0
    else:
        factor=1.0

    n_cells = array.shape[0]
    tensor2 = np.zeros((n_cells, 3, 3))
    tensor2[:, 0, 0] = array[:, 0] #11
    tensor2[:, 1, 1] = array[:, 1] #22
    tensor2[:, 2, 2] = array[:, 2] #33
    tensor2[:, 1, 2] = tensor2[:, 2, 1] = array[:, 3]/factor  #23
    tensor2[:, 0, 2] = tensor2[:, 2, 0] = array[:, 4]/factor  #13
    tensor2[:, 0, 1] = tensor2[:, 1, 0] = array[:, 5]/factor  #12
    return tensor2
