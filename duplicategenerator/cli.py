
import argparse
import logging
import os
import random
import sys
import pandas


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
  
  parser = argparse.ArgumentParser(prog = 'Duplicate generator', description='Duplicate generator commmand line tool')
  
  parser.add_argument("output_file", type = str, 
                      help="Name of the output file")
  
  parser.add_argument("num_originals", type = int, 
                      help="Number of original records to be created.")
  
  parser.add_argument("num_duplicates", type = int, 
                      help="Number of duplicate records to be created (maximum number is 9)")
  
  parser.add_argument("max_duplicate_per_record", type = int, 
                      help="The maximal number of duplicates that can becreated for one original record")
  
  parser.add_argument("max_modification_per_field", type = int, 
                      help="The maximum number of modifications per field")
  
  parser.add_argument("max_modification_per_record", type = int, 
                      help="The maximum number of modifications per record")
  
  parser.add_argument("distribution", choices=['uni', 'poi', 'zip','uniform', 'poisson','zipf'],
                      help="The probability distribution used to create the duplicates (i.e the number of duplicates for one original)")
  
  parser.add_argument("modification_types", type = str, choices=['typ', 'ocr', 'pho', 'all'],
                      help="Select the modification/error types that will be used when duplicates")
  
  parser.add_argument('--culture', type = str, default= None,
                      help="Select the country or culture from wich you want demographic data")
  
  parser.add_argument("--config_file", type = str, default = None,
                      help="Configuration file for the field to be generated")
   
  args = parser.parse_args()
   

  dupgen = DuplicateGen(
           int(args.num_originals),
           int(args.num_duplicates),
           int(args.max_duplicate_per_record),
           int(args.max_modification_per_field),
           int(args.max_modification_per_record),
           args.distribution,
           args.modification_types,
           False, # verbose
           args.culture,
           args.config_file,
           None) # field_names
  all_records = dupgen.generate(output = "dataframe")
  
  # WRITE CSV OUTPUT
  all_records.to_csv(args.output_file,)
  
if __name__=="__main__":
    execute_from_command_line()