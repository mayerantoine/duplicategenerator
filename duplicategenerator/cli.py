
import argparse
import logging
import os
import random
import sys
import pandas
import numpy
import json

from duplicategenerator.generate import DuplicateGen
from duplicategenerator import utils 
from duplicategenerator import config as cf

#from generate import DuplicateGen
#import utils 
#import config as cf


def write_csv_output(output_file,all_rec):
    """ 
    Write output file 
    
    Parameters
    ---------
    
    output_file : File path to save generated data
    all_rec : dictionary with all records generated 
    
    """
    # Get all record IDs and shuffle them randomly

    all_rec_ids = list(all_rec.keys())  
    random.shuffle(all_rec_ids)

    # Make a list of field names and sort them according to column number
    #
    field_name_list = ['rec_id']+self.field_names

    # Open output file
    #
    try:
      f_out = open(output_file, 'w',encoding="utf8")
    except:
      print('Error: Can not write to output file "%s"' % (output_file))
      sys.exit()

    # Write header line - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    if (cf.save_header == True):
      header_line = ''
      for field_name in field_name_list:
        header_line = header_line + field_name+ ', '
      header_line = header_line[:-2]
      f_out.write(header_line+os.linesep)

    # Loop over all record IDs
    #
    for rec_id in all_rec_ids:
      rec_dict = all_rec[rec_id]
      out_line = ''
      for field_name in field_name_list:

    #    if ((rec_dict.get(field_name, missing_value)).find(blank_value) < 0):
    #      out_line = out_line + rec_dict.get(field_name, missing_value) + ', '
    #    else:
    #      out_line = out_line + ' ' + ', '

        out_line = out_line + rec_dict.get(field_name, cf.missing_value) + ', '

        # To make original and duplicate records align column-wise
        #
        if (field_name == 'rec_id') and (out_line[-6:] == '-org, '):
          out_line += '  '

      # Remove last comma and space and add line separator
      #
      out_line = out_line[:-2]

      f_out.write(out_line+os.linesep)

    f_out.close()

    print('End.')


def execute_from_command_line():
  
 
  # =============================================================================
  # Start main program

  if (len(sys.argv) != 9):
    print('Height arguments needed with %s:' % (sys.argv[0]))
    print('  - Output file name')
    print('  - Number of original records')
    print('  - Number of duplicate records')
    print('  - Maximal number of duplicate records for one original record')
    print('  - Maximum number of modifications per field')
    print('  - Maximum number of modifications per record')
    print('  - Probability distribution for duplicates (uniform, poisson, zipf)')
    print('  - Type of modification (typo, ocr, phonetic, all)')
    print('All other parameters have to be set within the code')
    sys.exit()

  output_file =           sys.argv[1]
  num_org_records =       int(sys.argv[2])
  num_dup_records =       int(sys.argv[3])
  max_num_dups =          int(sys.argv[4])
  max_num_field_modifi =  int(sys.argv[5])
  max_num_record_modifi = int(sys.argv[6])
  prob_distribution =     sys.argv[7][:3]
  type_modification =     sys.argv[8][:3]


  if (num_org_records <= 0):
    print('Error: Number of original records must be positive')
    sys.exit()

  if (num_dup_records < 0):
    print('Error: Number of duplicate records must be zero or positive')
    sys.exit()

  if (max_num_dups <= 0) or (max_num_dups > 9):
    print('Error: Maximal number of duplicates per record must be positive and less than 10')
    sys.exit()

  if (max_num_field_modifi <= 0):
    print('Error: Maximal number of modifications per field must be positive')
    sys.exit()

  if (max_num_record_modifi <= 0):
    print('Error: Maximal number of modifications per record must be positive')
    sys.exit()

  if (max_num_record_modifi < max_num_field_modifi):
    print('Error: Maximal number of modifications per record must be equal to')
    print('       or larger than maximal number of modifications per field')
    sys.exit()

  if (prob_distribution not in ['uni', 'poi', 'zip']):
    print('Error: Illegal probability distribution: %s' % (sys.argv[7]))
    print('       Must be one of: "uniform", "poisson", or "zipf"')
    sys.exit()

  if (type_modification not in ['typ', 'ocr', 'pho', 'all']):
    print('Error: Illegal type of modification: %s' % (sys.argv[8]))
    print('       Must be one of: "typo, "ocr" or "pho" or "all"')
    sys.exit()

  dsgen = DuplicateGen(
           num_org_records,
           num_dup_records,
           max_num_dups,
           max_num_field_modifi,
           max_num_record_modifi,
           prob_distribution,
           type_modification,
           True,
           None,
           './duplicategenerator/config/attr_config_file.example.json',
           None)
  all_records = dsgen.generate(output = "dataframe")
  
  # WRITE CSV OUTPUT
  all_records.to_csv(output_file)
  
if __name__=="__main__":
    execute_from_command_line()