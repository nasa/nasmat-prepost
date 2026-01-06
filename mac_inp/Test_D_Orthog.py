"""function to verify orthogonality of three input vectors""" #pylint: disable=C0103
import numpy as np
from PyQt5.QtWidgets import QMessageBox  # pylint: disable=E0611

def test_d_orthog(sm,d1,d2,d3,err):
    """
    function to verify orthogonality of three input vectors

    Parameters:
        sm (int): material number
        D1,D2,D3 (np.ndarray): three input vectors
        err (float): tolerance for detecting error

    Returns:
        None.
    """
    msg=''
    dd1=np.dot(d1,d2)
    if abs(dd1)>=err:
        msg+=f"SM={sm} vectors D1,D2 not orthogonal, err={dd1}\n"
    dd2=np.dot(d1,d3)
    if abs(dd2)>=err:
        msg+=f"SM={sm} vectors D1,D3 not orthogonal, err={dd2}\n"
    dd3=np.dot(d2,d3)
    if abs(dd3)>=err:
        msg+=f"SM={sm} vectors D2,D3 not orthogonal, err={dd3}\n"

    if msg:
        QMessageBox.warning(None,"Warning",msg[:-1])
