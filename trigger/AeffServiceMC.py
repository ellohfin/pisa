#
# Creates the effective areas from a simfile, then returns them
# re-scaled as desired.
#
# author: Timothy C. Arlen
# 
# date:   April 8, 2014
#

import logging
import numpy as np
from utils.utils import get_bin_centers, get_bin_sizes
import h5py
import os,sys

class AeffServiceMC:
    '''
    Takes the weighted effective area files, and creates a dictionary
    of the 2D effective area in terms of energy and coszen, for each
    flavor (nue,nue_bar,numu,...) and interaction type (CC, NC)
    
    The final aeff dict for each flavor is in units of [m^2] in each
    energy/coszen bin.
    '''
    def __init__(self,ebins,czbins,aeff_file=None,**kwargs):
        self.ebins = ebins
        self.czbins = czbins
        
        logging.info('Opening file: %s'%(aeff_file))
        aeff_file = os.path.expandvars(aeff_file)
        try:
            fh = h5py.File(aeff_file,'r')
        except IOError,e:
            logging.error("Unable to open aeff_file %s"%aeff_file)
            logging.error(e)
            sys.exit(1)

        self.aeff_dict = {}
        logging.info("Creating effective area dict...")
        for flavor in ['nue','nue_bar','numu','numu_bar','nutau','nutau_bar']:
            flavor_dict = {}
            logging.debug("Working on %s effective areas"%flavor)
            for int_type in ['cc','nc']:
                weighted_aeff = np.array(fh[flavor+'/'+int_type+'/weighted_aeff'])
                true_energy = np.array(fh[flavor+'/'+int_type+'/true_energy'])
                true_coszen = np.array(fh[flavor+'/'+int_type+'/true_coszen'])
                
                bins = (self.ebins,self.czbins)
                aeff_hist,_,_ = np.histogram2d(true_energy,true_coszen,
                                               weights=weighted_aeff,bins=bins)
                # Divide by bin widths to convert to aeff:
                ebin_sizes = get_bin_sizes(ebins)
                czbin_sizes = 2.0*np.pi*get_bin_sizes(czbins)
                bin_sizes = np.meshgrid(czbin_sizes,ebin_sizes)
                aeff_hist /= np.abs(bin_sizes[0]*bin_sizes[1])
                
                flavor_dict[int_type] = aeff_hist
                
            self.aeff_dict[flavor] = flavor_dict
            
        return
    
    def get_aeff(self,*kwargs):
        '''
        Returns the effective area dictionary
        '''

        return self.aeff_dict
        
        
