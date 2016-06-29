#!/usr/bin/env python
#
#

#================================================================================
#
# Imports
#
#================================================================================
import os
import sys
import shutil
import subprocess as sp

codedir = '/home/marchdf/dg1d/src/'
sys.path.insert(0, codedir)
import deck as deck

#================================================================================
#
# Function definitions
#
#================================================================================
def runcode(deck):
    """Run the DG code given the input deck"""

    # Launch the code
    log = open('logfile', "w")
    proc = sp.Popen(codedir+'main.py -d '+deck, shell=True, stdout=log,stderr=sp.PIPE)

    # Wait for it to end and get the output
    retcode = proc.wait()
    log.flush()

    return retcode

    
#================================================================================
#
# Problem setup
#
#================================================================================
basedir = os.getcwd()
datadir = basedir

orders = [2]
resolutions = [1024] #[8,16,32,64,128,256,512] #[8,16,32,64,128,256,512] # [32768] #[8,16,32,64,128,256,512,1024,2048,4096,8192,16384]


for p, order in enumerate(orders):
    for k,res in enumerate(resolutions):
    

        # problem definitions
        defs = [ ['PDE system' , 'advection'],
                 ['initial condition' , 'sinewave '+str(res)],
                 ['number of outputs' , '11'],
                 ['final time', '2'],
                 ['Courant-Friedrichs-Lewy condition' , '0.5'],
                 ['order' , str(order)],
                 ['limiting' , '0']]


        # working directory for the data
        workdir =  datadir + '/' + str(order)+'/'+str(res)
        print('Creating directory',workdir,'and go to it')
        shutil.rmtree(workdir, ignore_errors=True)
        os.makedirs(workdir)
        os.chdir(workdir)
        
        # create the deck
        deckname = deck.write_deck(workdir,defs)
        
        # run the code
        runcode(deckname)
        
        # Go back to our base directory
        os.chdir(basedir)

