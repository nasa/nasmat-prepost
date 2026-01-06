""" Functions used for determining model hierarchy"""

#Get the model hierarchy from NASMAT inputs
def get_model_hierarchy(deck,mode,maxlev=None):
    """
    function to get model hierachy for UI

    Parameters:
        deck (dict): parameters related to NASMAT deck
        mode (bool): hiearchy type
                     True  - shortened version, no duplicate RUCs at level
                     False - full version, all model RUCs (including repeats)
        maxlev (int): maximum level to stop hierarchy (cutoff)

    Returns:
        hrchy (dict): hierarchy showing parent/child relationships
        hrchy_items (dict): data for each item in hierarchy
        hstr (dict, list , str): string(s) giving names of items in hierarchy
    """

    hrchy={}
    hrchy_items={}
    item=[0]
    iruc=[1]
    mat=0
    rucs=deck['ruc']['rucs']
    rmap=deck['ruc_map']
    n_rucs=1
    lvl=1
    parent_item='0'

    hstr=[]
    if mode: #from keyword
        _get_kw_hierarchy(hrchy,hrchy_items,item,rucs,mat,lvl,parent_item,n_rucs)
        _convert_hierarchy(hstr,hrchy,hrchy_items,mode)
    else: #from results
        ruc=rucs['0']
        parent={'lvl':1,'dim':ruc['DIM'],'deck_ruc':rmap['0'],'ruc':1,
                'matnum':0,'subvol':1,'ia':1,'ib':1,'ig':1,
                'parent-NB':1,'parent-NG':1}
        _get_res_hierarchy(hrchy,hrchy_items,rucs,rmap,parent,iruc,maxlev=maxlev)
        _convert_hierarchy(hstr,hrchy,hrchy_items,mode,maxlev)
    hstr=hstr[0]

    return hrchy,hrchy_items,hstr


def _get_dof(mod,na,nb,ng,vect=False):
    """
    function to get degrees of freedom per micromechanics method

    Parameters:
        mod (int): NASMAT *RUC mod parameter
        na,nb,ng (int): number of subvol in each direction for unit cell
        vect (bool): flag to set vector-based dof (only one method now)

    Returns:
        dof (int): number of degrees of freedom for selected method
    """

    if vect:
        dof=3*na*nb*ng + nb*ng + na*ng + na*nb
        return dof

    dof=-1
    if mod==102: #gmc2d
        dof=nb+ng
    elif mod==103: #gmc3d
        dof=nb*ng + na*ng + na*ng + na + nb + ng
    elif mod==202: #hfgmc2d
        dof=6*nb*ng + 3*(nb+ng)
    elif mod==203: #hfgmc3d
        dof=9*na*nb*ng + 3*(nb*ng + na*ng + na*nb)
    elif mod in (2,3):
        dof=12
    else:
        raise ValueError('dof not defined for micromechanics method')

    return dof

#determine the model hierarchy from keyword input (no duplicates)
def _get_kw_hierarchy(hrchy,hrchy_items,item,rucs,mat,lvl,parent,n_lower_rucs):
    """
    function to get keywords-based hierarchy

    Parameters:
        hrchy (dict): hierarchy showing parent/child relationships
        hrchy_items (dict): data for each item in hierarchy
        item
        rucs (dict): all RUC parameters
        mat (int): actual material number
        lvl (int): NASMAT level
        parent (dict): parent RUC parameters
        n_lower_rucs (int): number of lower level RUCs within current RUC

    Returns:
        None.
    """
    ruc = rucs[str(mat)]
    all_mats=ruc['all_mats_uniq']
    msms=all_mats[all_mats<0].tolist()
    counts=ruc['all_mats_uniq_cnt']
    lower_ruc_count={}
    for value, count in zip(all_mats, counts):
        lower_ruc_count[value]=count


    hrchy[str(item[0])]={} #hierarchy structure
    hrchy_items[str(item[0])]={} #hierarchy items
    hrchy_items[str(item[0])]['lvl']=lvl
    hrchy_items[str(item[0])]['dim']=ruc['DIM']
    hrchy_items[str(item[0])]['matnum']=mat
    hrchy_items[str(item[0])]['n_subvol']= ruc['na']*ruc['nb']*ruc['ng']
    hrchy_items[str(item[0])]['n_dof']=_get_dof(ruc['mod'],ruc['na'],ruc['nb'],ruc['ng'])
    hrchy_items[str(item[0])]['n_lower_rucs']=n_lower_rucs
    hrchy_items[str(item[0])]['parent']=parent

    if msms:
        msms.sort()
        jlvl=lvl+1
        newparent=str(item[0])
        for msm in msms:
            item[0]+=1
            nn_lower_rucs = lower_ruc_count[msm]
            _get_kw_hierarchy(hrchy[newparent],hrchy_items,item,rucs,
                                msm,jlvl,newparent,nn_lower_rucs)


#determine the model hierarchy from unique results
def _get_res_hierarchy(hrchy,hrchy_items,rucs,rmap,parent,iruc,maxlev=None):
    """
    function to get results-based hierarchy

    Parameters:
        hrchy (dict): hierarchy showing parent/child relationships
        hrchy_items (dict): data for each item in hierarchy
        rucs (dict): all RUC parameters
        rmap (dict): maps material number to RUC number
        parent (dict): parent RUC parameters
        iruc (list): RUC counter
        maxlev (int): maximum level to stop hierarchy (cutoff)

    Returns:
        None.
    """

    ruc=rucs[str(parent['matnum'])]
    dim=ruc['DIM']
    all_mats=ruc['all_mats']

    if (not maxlev or (maxlev and parent['lvl']<=maxlev)):
        hrchy[str(parent['ruc'])]={} #hierarchy structure
        hrchy_items[str(parent['ruc'])]=parent #hierarchy items
        maxlev_reached=False
    else:
        maxlev_reached=True


    jlvl=parent['lvl']+1

    isv=0
    for ia in range(ruc['na']):
        for ib in range(ruc['nb']):
            for ig in range(ruc['ng']):
                isv+=1
                matnum = -1
                if dim=='2D':
                    matnum=all_mats[ib][ig]
                elif dim=='3D':
                    matnum=all_mats[ig][ib][ia]
                elif dim=='MT':
                    matnum=all_mats[ig][ib][ia]

                if matnum<0:
                    iruc[0]+=1
                    rid=rmap[str(matnum)]
                    new_dim=rucs[str(matnum)]['DIM']
                    child={'lvl':jlvl,'dim':new_dim,'deck_ruc':rid,'ruc':iruc[0],'matnum':matnum,
                           'subvol':isv,'ia':ia+1,'ib':ib+1,'ig':ig+1,
                           'parent-NB':ruc['nb'],'parent-NG':ruc['ng']}
                    if maxlev_reached:
                        _get_res_hierarchy({},hrchy_items,rucs,rmap,child,iruc,maxlev)
                    else:
                        _get_res_hierarchy(hrchy[str(parent['ruc'])],hrchy_items,rucs,
                                            rmap,child,iruc,maxlev)

def _convert_hierarchy(hrchy_str_old,hrchy,hrchy_items,mode=True,maxlev=None):
    """
    function to convert the hierarchy to string form for UI

    Parameters:
        hrchy_str_old (list): hierarchy in form used by UI
        hrchy (dict): hierarchy showing parent/child relationships
        hrchy_items (dict): data for each item in hierarchy
        mode (bool): hiearchy type
                     True  - shortened version, no duplicate RUCs at level
                     False - full version, all model RUCs (including repeats)
        maxlev (int): maximum level to stop hierarchy (cutoff)

    Returns:
        None.
    """

    for key in hrchy.keys():
        item=hrchy_items[key]
        dim=item['dim']
        lvl=item['lvl']
        mat=item['matnum']

        if mode: #keyword format
            keystr=f"Level {lvl} {dim} RUC - M={mat}"
        else: #results format
            rid=item['deck_ruc']
            isv=item['subvol']
            jruc=item['ruc']
            keystr=f"Level {lvl} {dim} RUC ({rid}) - M={mat},SubVol.:{isv},RUCID:{jruc}"

        hrchy_str_new=[]
        if ((mode) or (not mode and maxlev and lvl<=maxlev)):
            _convert_hierarchy(hrchy_str_new,hrchy[key],hrchy_items,mode,maxlev)
        if hrchy_str_new:
            hrchy_str_old.append({keystr:hrchy_str_new})
        else:
            hrchy_str_old.append(keystr)
