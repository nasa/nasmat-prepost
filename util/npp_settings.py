"""File to get/set default NASMAT PrePost settings"""
import os

def get_npp_settings(env_file=None,echo=False):
    """
    function to get default NASMAT PrePost settings

    Parameters:
        env_file (str): environment file for NASMAT PrePost
        echo (bool): logical to output settings as input

    Returns:
        npp_settings (dict): default NASMAT PrePost settings
    """

    if not env_file:
        env_file='NASMATPrePost.env'

    npp_settings = {}

    if os.path.isfile(env_file):
        with open(env_file, "r", encoding='utf-8') as f:
            for line in f:
                if '=' in line:
                    if echo:
                        print(line.strip())
                    key, value = line.strip().split("=", 1)
                    npp_settings[key] = value

    if 'BACKGROUND_COLOR' in npp_settings:
        b = npp_settings['BACKGROUND_COLOR'].split(',')
        npp_settings['BACKGROUND_COLOR']=[float(c) for c in b]

    if 'COLORMAP' in npp_settings:
        npp_settings['COLORMAP']=int(npp_settings['COLORMAP'])

    return npp_settings


def write_npp_settings(npp_settings=None,env_file=None,echo=False):
    """
    function to write default NASMAT PrePost settings

    Parameters:
        env_file (str): environment file for NASMAT PrePost
        npp_settings (dict): NASMAT PrePost settings
        echo (bool): logical to output settings as input

    Returns:
        None.
    """
    if not npp_settings or not env_file:
        return

    with open(env_file, "w", encoding='utf-8') as f:
        for key,value in npp_settings.items():
            if isinstance(value,(int,float)):
                value = str(value)
            elif isinstance(value,list):
                value = ",".join(map(str, value))
            f.write(f"{key}={value}\n")
            if echo:
                print(f"{key}={value}")
