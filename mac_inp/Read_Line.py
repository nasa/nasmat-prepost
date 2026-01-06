"line reader for MAC files" #pylint: disable=C0103
def read_line(f):
    """
    function to read a line or lines in MAC files

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        d (str): ouput line after cleanup
        comments (list): any comments detected
    """
    comments=[]
    d = f.readline().lstrip().rstrip()

    while d.startswith('#'):
        comments.append(d)
        d = f.readline().lstrip().rstrip()
    while d.endswith('&'):
        d=d[:-1].rstrip()+' '
        d2=f.readline().lstrip().rstrip()
        while d2.startswith('#'):
            comments.append(d2)
            d2=f.readline().lstrip().rstrip()
        if d2[0:1].isdigit() and not d.rstrip().endswith(','):
            d=d+','+d2
        else:
            d=d+d2

    return d,comments
