""" helper function to get NASMAT *.out output values"""
import re
import numpy as np

def output_parser(fname,lam=False):
    """
    function to parse NASMAT output for various quantities

    Parameters:
        fname (str): name of NASMAT *.out file
        lam (bool): flag to read *LAMINATE output
    
    Returns:
        d (dict): output values found in NASMAT *.out file
    """

    d={}
    #hard-coded values to search for. Use as a template for making additions
    if lam:
        pattern = re.compile(r'(Exx|Eyy|Nxy|Gxy)\s*=\s*|Elapsed\s+(.+?)\s*=\s*')
    else:
        pattern = re.compile(
            r'(E11S|N12S|N13S|E22S|N23S|E33S|G23S|G12S|G13S|K11S|K22S|K33S)\s*=\s*'
            r'|Elapsed\s+(.+?)\s*=\s*')

    #search file for requested outputs
    d['ERROR']=False
    with open (fname, 'rt', encoding='UTF-8') as f:
        for line in f:
            if pattern.search(line) is not None:
                line=line.replace(" ", "").rstrip()
                if 'seconds' in line:
                    line=line.split('seconds')[0]
                d[line[:line.find('=')]]=np.array(float(line[line.find('=')+1:]))
                #print('fname= %s'%(fname), line)
            else:
                if '*****ERROR*****' in line:
                    d['ERROR'] = True

    return d
