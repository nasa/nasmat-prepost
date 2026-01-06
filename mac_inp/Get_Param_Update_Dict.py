"""
function to parse a string and update dictionary
#delim1 separates parameters
#delim2 separates value from single parameter
""" #pylint: disable=C0103
def get_param_update_dict(s,d,delim1,delim2):
    """
    function parse a string and update dict

    Parameters:
        s (str): input string
        d (dict): input dict
        delim1 (str): first delimeter serpating parameters
        delim2 (str): second delimeter serpating values

    Returns:
        d (dict): updated dict
    """
    n=[x.split(delim2) for x in s.split(delim1)]

    #adding logic to account for extra delim1 values
    #removing blank entries
    n = [nn for nn in n if nn[0]]
    #consolidating strings
    i = 1
    while i < len(n):
        if len(n[i]) == 1:
            n[i-1][1] += n[i][0]
            n.pop(i)
        else:
            i += 1
    #updating dict - logic may need to be updated based on your input file
    # files may work with NASMAT, but have issues with reading here
    for key, val in n:
        key_lower = key.lower()
        if '.' in val and ',' not in val and key_lower != 'name':
            d[key_lower] = float(val)
        elif '.' in val and ',' in val:
            l = val.split(',')
            d[key_lower] = [float(el) for el in l]
        elif '.' not in val and ',' in val:
            l = val.split(',')
            d[key_lower] = [int(el) for el in l]
        elif val.isalpha() or key_lower == 'name':
            d[key_lower] = val
        elif '.' not in val and 'e' in val.lower():
            l = val.split(',')
            d[key_lower] = [float(el) for el in l]
        else:
            d[key_lower] = int(val)

    return d
