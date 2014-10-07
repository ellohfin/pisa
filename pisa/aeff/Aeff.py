#! /usr/bin/env python
#
# Aeff.py
#
# This module is the implementation of the stage2 analysis. The main
# purpose of stage2 is to combine the "oscillated Flux maps" with the
# effective areas to create oscillated event rate maps, using the true
# information.
# 
# If desired, this will create a .json output file with the results of
# the current stage of processing.
#
# author: Timothy C. Arlen
#
#         tca3@psu.edu
#
# date:   April 8, 2014
#

import os,sys
import numpy as np
import logging
from argparse import ArgumentParser, RawTextHelpFormatter
from pisa.utils.utils import set_verbosity, check_binning, get_binning
from pisa.utils.jsons import from_json, to_json
from pisa.utils.proc import report_params, get_params, add_params
from pisa.aeff.AeffServiceMC import AeffServiceMC
from pisa.aeff.AeffServicePar import AeffServicePar
from scipy.constants import Julian_year


def get_event_rates(osc_flux_maps,aeff_service,livetime=1.0,nu_xsec_scale=1.0,
                    nubar_xsec_scale=1.0,aeff_scale=1.0,**kwargs):
    '''
    Main function for this module, which returns the event rate maps
    for each flavor and interaction type, using true energy and zenith
    information. The content of each bin will be the weighted aeff
    multiplied by the oscillated flux, so that the returned dictionary
    will be of the form:
    {'nue': {'cc':map,'nc':map},
     'nue_bar': {'cc':map,'nc':map}, ...
     'nutau_bar': {'cc':map,'nc':map} }
    '''
    
    #Get parameters used here
    params = get_params()
    report_params(params,units = ['','yrs','',''])

    #Initialize return dict
    event_rate_maps = {'params': add_params(params,osc_flux_maps['params'])}

    #Get effective area
    aeff_dict = aeff_service.get_aeff()
    
    ebins, czbins = get_binning(osc_flux_maps)
    
    # apply the scaling for nu_xsec_scale and nubar_xsec_scale...
    flavours = ['nue','numu','nutau','nue_bar','numu_bar','nutau_bar']
    for flavour in flavours:
        osc_flux_map = osc_flux_maps[flavour]['map']
        int_type_dict = {}
        for int_type in ['cc','nc']:
            event_rate = osc_flux_map*aeff_dict[flavour][int_type]*aeff_scale
            
            scale = nubar_xsec_scale if 'bar' in flavour else nu_xsec_scale
            event_rate *= (scale*livetime*Julian_year)
            int_type_dict[int_type] = {'map':event_rate,
                                       'ebins':ebins,
                                       'czbins':czbins}
        event_rate_maps[flavour] = int_type_dict
        
    return event_rate_maps

if __name__ == '__main__':

    parser = ArgumentParser(description='Take an oscillated flux file '
                          'as input & write out a set of oscillated event counts. ',
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('osc_flux_maps',metavar='FLUX',type=from_json,
                     help='''JSON osc flux input file with the following parameters:
      {"nue": {'czbins':[], 'ebins':[], 'map':[]}, 
       "numu": {...},
       "nutau": {...},
       "nue_bar": {...},
       "numu_bar": {...},
       "nutau_bar": {...} }''')
    parser.add_argument('--weighted_aeff_file',metavar='WEIGHTFILE',type=str,
                        default='events/V15_weighted_aeff.hdf5',
                        help='''HDF5 File containing event data for each flavours for
                        a particular instrumental geometry. The effective area
                        is calculate from the event weights in this file.
                        Only applies in non-parametric mode.''')
    parser.add_argument('--settings_file',metavar='SETTINGS',type=str,
                        default='aeff/V15_aeff.json',
                        help='''json file containing parameterizations of the
                         effective area and its cos(zenith) dependence.
                         Only applies in parametric mode.''')
    parser.add_argument('--livetime',type=float,default=1.0,
                        help='''livetime in years to re-scale by.''')
    parser.add_argument('--nu_xsec_scale',type=float,default=1.0,
                        help='''Overall scale on nu xsec.''')
    parser.add_argument('--nubar_xsec_scale',type=float,default=1.0,
                        help='''Overall scale on nu_bar xsec.''')
    parser.add_argument('--aeff_scale',type=float,default=1.0,
                        help='''Overall scale on aeff''')
    parser.add_argument('--parametric',action='store_true', default=False,
                        help='''Use parametrized effective areas instead of
                        extracting them from event data.''')
    parser.add_argument('-o', '--outfile', dest='outfile', metavar='FILE', type=str,
                        action='store',default="event_rate.json",
                        help='''file to store the output''')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='''set verbosity level''')
    args = parser.parse_args()

    #Set verbosity level
    set_verbosity(args.verbose)
        
    #Check binning
    ebins, czbins = check_binning(args.osc_flux_maps)

    logging.info("Defining aeff_service...")
    
    if args.parametric:
        logging.info("  Using effective area from PARAMETRIZATION...")
        aeff_service = AeffServicePar(ebins,czbins,settings_file=args.settings_file)
    else:
        logging.info("  Using effective area from EVENT DATA...")
        aeff_service = AeffServiceMC(ebins,czbins,simfile=args.weighted_aeff_file)
        
    event_rate_maps = get_event_rates(args.osc_flux_maps,aeff_service,args.livetime,
                                      args.nu_xsec_scale,args.nubar_xsec_scale,
                                      args.aeff_scale)
    
    logging.info("Saving output to: %s"%args.outfile)
    to_json(event_rate_maps,args.outfile)
    
    
