"""Class for detecting and substitituing in NASMAT parameters"""
import os
import re
import ast
import operator as op
import numpy as np

class SubParam():
    """
    NASMAT parameter detection and substitution tool

    In the MAC file, denote any parameters with unique names within braces. 
    Expressions can also be evaulated. 
    
    The code expects default values for all variables to be defined in the MAC file
    (in no more than one place) if not supplying updated values. Default values can
    be included after the *END keyword for convenience without impacting the execution
    of NASMAT.

    E.g., see the E_M and NU_M parameters defined below

    *CONSTITUENTS
     NMATS=1
     #-- Matrix
     M=1 CMOD=6 MATID=U MATDB=1 &
     EL={E_M=3.0E3},{E_M},{NU_M=0.3},{NU_M},{0.5*E_M/(1+NU_M)},45.0E-6,45.0E-6
  
    """
    def __init__(self,param_mac,update_param=None,workdir='./',fileid=1):
        """
        initialization routine for class

        Parameters:
            param_mac (str): MAC input file containing parameters
            update_param (dict): updates parameters from param_mac file with new values
            workdir (str): working directory
            fileid (int): ID number to append to file name after parameter substitution.

        Returns:
            None.
        """

        #Store input variables
        self.workdir=workdir
        self.param_mac=param_mac
        self.update_param=update_param
        if self.update_param:
            for key,value in self.update_param.items():
                if not isinstance(self.update_param[key],str):
                    self.update_param[key] = str(value)
        self.fileid=fileid
        #allowed operation for later evaluations
        self.ops = {
            ast.Add: op.add,
            ast.Sub: op.sub,
            ast.Mult: op.mul,
            ast.Div: op.truediv,
            ast.Pow: op.pow,
            ast.USub: op.neg,
            ast.UAdd: op.pos,
            ast.Mod: op.mod,
            ast.FloorDiv: op.floordiv,
        }

        #Switch to working directory
        os.chdir(workdir)
        #Extract parameters from file
        d=self.get_params(self.param_mac)
        #Set new parameters
        p=self.set_params(d)
        #Create new file with substitutions added
        newfile=p['file'][:-4]+f"_{self.fileid}.MAC"
        p['file']=newfile
        self.make_new_file(p)

    def get_params(self,file):
        """
        function to extract parameters from files

        Parameters:
            d (dict): inputs defining parameters and type      

        Returns:
            p (dict): updated dict containing output values
        """

        d=[]
        with open(file,'r',encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                m = re.findall(r'{(?:[^{}])*}',line)
                for mm in m:
                    d.append(mm[1:-1])

        #Calculate unique values in list
        du1=list(set(d))

        #define mapping dict
        mapping = {}
        for item in du1:
            if '=' in item:
                key, val = item.split('=', 1)
                mapping[key] = item

        du1 = [mapping.get(x.split('=', 1)[0], x) for x in du1]
        du = list(set(du1))

        #Search for defined default values
        defval = []
        for i, s in enumerate(du):
            if '=' in s:
                key, val = s.split('=', 1)
                du[i] = key
                defval.append(val)
            else:
                defval.append("n/a")

        #Sort through and determine any calculations to be performed
        ops = ['+','-','/','*']
        param_calc=np.zeros(len(du),dtype=int)
        for i,p in enumerate(du):
            #check if ops are in p
            if any(x in p for x in ops):
                param_calc[i]=1

        if self.update_param:
            for m in self.update_param.keys():
                try:
                    ind=du.index(m)
                except ValueError:
                    continue
                defval[ind]=self.update_param[m]

        d={}
        d['p']=du
        d['n_parms']=len(d['p'])
        d['p_calc']=param_calc
        d['defval']=defval
        d['lines']=lines
        d['file']=file
        return d

    def safe_eval(self,expr):
        """
        function to safely evaluate an expression

        Parameters:
            expr (str): input string to be evaluated      

        Returns:
            float or int: evaluation of input expression

        """

        def _eval(node):
            if isinstance(node, ast.Num):       # numbers
                return node.n
            if isinstance(node, ast.UnaryOp):   # -n, +n
                return self.ops[type(node.op)](_eval(node.operand))
            if isinstance(node, ast.BinOp):     # n + n, etc.
                return self.ops[type(node.op)](_eval(node.left), _eval(node.right))
            raise ValueError("Unsafe expression")

        return _eval(ast.parse(expr, mode='eval').body)

    def set_params(self,d):
        """
        function to set parameter values

        Parameters:
            d (dict): inputs defining parameters and type      

        Returns:
            p (dict): updated dict containing output values
        """

        p=d
        #Assign values for output (1st loop, default)
        p['outval']=[]
        for i in range(p['n_parms']):
            if p['defval'][i]=='n/a' and p['p_calc'][i]==0: #prompt for input
                p['outval'].append(input(f"Input a value for {p['p'][i]}: "))
            elif p['defval'][i]=='n/a' and p['p_calc'][i]==1: #expression
                p['outval'].append('expression') #to be evaluated next (after all inputs read)
            else:
                p['outval'].append(p['defval'][i])
        #Evaluate any expressions
        for i in range(p['n_parms']):
            if p['outval'][i]=='expression':
                exp=p['p'][i]
                for j in range(p['n_parms']):
                    if p['p'][j] in exp and not p['p_calc'][j]:
                        exp=exp.replace(p['p'][j], p['outval'][j])
                p['outval'][i]=f"{self.safe_eval(exp):12E}"
        return p

    def make_new_file(self,p):
        """
        function create new file by substituing parameters

        Parameters:
            d (dict): inputs defining parameters and type      

        Returns:
            p (dict): updated dict containing output values
        """

        with open(p['file'],'w+',encoding='utf-8') as f:
            for line in p['lines']:
                m = re.findall(r'{(?:[^{}])*}',line)
                for mm in m:
                    if '=' in mm:
                        mms=mm[1:mm.index('=')]
                        ind=p['p'].index(mms)
                    else:
                        ind=p['p'].index(mm[1:-1])

                    val=p['outval'][ind]
                    line=line.replace(mm,val)
                f.write(line)
