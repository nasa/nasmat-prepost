"""function to get values after equal sign""" #pylint: disable=C0103
def get_after_eqsign(f):
    """
    function to get values after equal sign

    Parameters:
        f (io.TextIOWrapper): opened file to read

    Returns:
        None.
    """

    #handle lines with comments
    while True:
        d = f.readline()
        if not d:
            return None
        d = d.strip()
        if d and not d.startswith('#'):
            break

    #handle lines with the & continuation character
    parts = []
    while True:
        continued = d.endswith('&')
        if continued:
            d = d[:-1].rstrip()

        parts.append(d)

        if not continued:
            break

        while True:
            d = f.readline()
            if not d:
                break
            d = d.strip()
            if d and not d.startswith('#'):
                break

    d = ' '.join(parts)
    _, rhs = d.split('=', 1)

    return rhs.strip()
