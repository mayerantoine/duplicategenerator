#! /usr/bin/env python3
# =============================================================================
# AUSTRALIAN NATIONAL UNIVERSITY OPEN SOURCE LICENSE (ANUOS LICENSE)
# VERSION 1.3
# 
# The contents of this file are subject to the ANUOS License Version 1.3
# (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at:
# 
#   https://sourceforge.net/projects/febrl/
# 
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and limitations
# under the License.
# 
# The Original Software is: "generate2.py"
# 
# The Initial Developers of the Original Software are:
#   Dr Peter Christen (Research School of Computer Science, The Australian
#                      National University)
#   Mr Agus Pudjijono (Department of Computer Science, The Australian
#                      National University)
# 
# Copyright (C) 2002 - 2011 the Australian National University and
# others. All Rights Reserved.
# 
# Contributors:
# 
# Alternatively, the contents of this file may be used under the terms
# of the GNU General Public License Version 2 or later (the "GPL"), in
# which case the provisions of the GPL are applicable instead of those
# above. The GPL is available at the following URL: http://www.gnu.org/
# If you wish to allow use of your version of this file only under the
# terms of the GPL, and not to allow others to use your version of this
# file under the terms of the ANUOS License, indicate your decision by
# deleting the provisions above and replace them with the notice and
# other provisions required by the GPL. If you do not delete the
# provisions above, a recipient may use your version of this file under
# the terms of any one of the ANUOS License or the GPL.
# =============================================================================
#
# Freely extensible biomedical record linkage (Febrl) - Version 0.4.2
#
# See: http://datamining.anu.edu.au/linkage.html
#
# =============================================================================

"""Module generate2.py - Auxiliary program to create records using various
                         frequency tables and introduce duplicates with errors.

   USAGE:
     python generate2.py [output_file] [num_originals] [num_duplicates]
                         [max_duplicate_per_record]
                         [max_modification_per_field]
                         [max_modification_per_record] [distribution]
                         [modification_types] [num_fam_household_records]

   ARGUMENTS:
     output_file                  Name of the output file (currently this is a
                                  CSV file).
     num_originals                Number of original records to be created.
     num_duplicates               Number of duplicate records to be created
                                  (maximum number is 9).
     max_duplicate_per_record     The maximal number of duplicates that can be
                                  created for one original record.
     max_modification_per_field   The maximum number of modifications per field
     max_modification_per_record  The maximum number of modifications per
                                  record.
     distribution                 The probability distribution used to create
                                  the duplicates (i.e the number of duplicates
                                  for one original).
                                  Possible are: - uniform
                                                - poisson
                                                - zipf
     modification_types           Select the modification/error types that will
                                  be used when duplicates and family/household
                                  records are generated.
                                  Possible re: - typ (typographical errors)
                                               - ocr (OCR errors)
                                               - pho (phonetical errors)
                                               - all (all error types)
     num_fam_household_records    The number of family and household records to
                                  be generated.


   DESCRIPTION:
     This program can be used to create a data set with records that contain
     randomly created names and addresses (using frequency files), dates,
     phone numbers, and identifier numbers. Duplicate records will then be
     created following a given probability distribution, with different single
     errors being introduced.

     Various parameters on how theses duplicates are created can be given
     within the program, see below.

     It is possible to load dictionaries (look-up table) with misspellings that
     will be used to replace a correct word with a randomly chosen misspelling.
     A user can easily customise this misspelling files.

     New: Version 2 (generate2) of this generator now include field
          dependencies, the possibilities to model phonetic, OCR and
          typographical modifications, as well as to generate family and
          household data.

          These functionalities are in an 'alpha' state and have received
          limited testing. They have been implemented by Agus Pudjijono. For
          more detailed descriptions please see:

            Probabilistic Data Generation
            Agus Pudjijono
            Master of Computing (Honours) thesis,
            ANU Department of Computer Science, November 2008.

          as available from:

            http://datamining.anu.edu.au/projects/linkage-publications.html

   NOTE: Depending upon parameter settings it is possible that the program
         'hangs' when generating duplicate or family/household records. This
         is because due to the randomness of the records generated it is not
         possible to select another 'original' record for modification. The
         remedy currently is to stop the program and re-start it, possibly
         with different parameter settings (like smaller number of duplicates
         or family/household records, or larger number of original records).

   TODO:
     - fix problem of endless loop when randomly selecting duplicate or
       family/household records.

     - add substitution matrix with character substitution probabilities
       (instead of keyboard based substitutions).

     - Improve performance (loading and creating frequency tables)

     - for each field have a counter num_modifcations in the field dictionary

     - do swap between field first (count as 2 rec. modifications)

     - Allow various probability distributions for fields of type 'date' and
       'iden' (using a new keyword in field dictionaries).

     - Try to find real world error distributions for typographical errors and
       integrate them into the random error creation

     - Add random word spilling between fields (similar to field swapping)
"""

# =============================================================================
# Imports go here

import copy
import math
import random
import string
import sys
import time
import utils 
import os
import config as cf

# Set this flag to True for verbose output, otherwise to False - - - - - - - -
#
VERBOSE_OUTPUT = True


# =============================================================================
# Nothing to be changed below here
# =============================================================================



class DataSetGen:
  
  def __init__(self,output_file,
             num_org_records,
             num_dup_records,
             max_num_dups,
             max_num_field_modifi,
             max_num_record_modifi,
             prob_distribution,
             type_modification,
             num_of_hofam_duplicate):
    
    self.output_file = output_file
    self.num_org_records = num_org_records
    self.num_dup_records = num_dup_records
    self.max_num_dups = max_num_dups
    self.max_num_field_modifi = max_num_field_modifi
    self.max_num_record_modifi = max_num_record_modifi
    self.prob_distribution = prob_distribution
    self.type_modification = type_modification
    self.num_of_hofam_duplicate = num_of_hofam_duplicate
    
    self.field_names = []  # Make a list of all field names

  def _validate_and_sum_prob(self)  :
      """ Check all user options within generate.py for validity  """
            
      # A list of all probabilities to check ('select_prob' is checked separately)
      prob_names = ['ins_prob','del_prob','sub_prob','trans_prob','val_swap_prob',
                    'wrd_swap_prob','spc_ins_prob','spc_del_prob','miss_prob',
                    'misspell_prob','new_val_prob']

      select_prob_sum = 0.0  # Sum over all select probabilities

      # Check if all defined field dictionaries have the necessary keys
      # check name , type , char range, select_prob and prob
      # returns select_prob_sum, update field_dict and field_names
      i = 0  # Loop counter
      for field_dict in cf.field_list:

        #  field name
        if ('name' not in field_dict):
          print('Error: No field name given for field dictionary')
          raise Exception
        elif (field_dict['name'] == 'rec_id'):
          print('Error: Illegal field name "rec_id" (used for record identifier)')
          raise Exception
        else:
          self.field_names.append(field_dict['name'])

        # field type
        if (field_dict.get('type','') not in ['freq','date','phone','ident','others']):
          print('Error: Illegal or no field type given for field "%s": %s' % (field_dict['name'], field_dict.get('type','')))
          raise Exception

        # field char_range
        if (field_dict.get('char_range','') not in ['alpha', 'alphanum','digit']):
          print('Error: Illegal or no random character range given for ' + 'field "%s": %s' % (field_dict['name'], field_dict.get('char_range','')))
          raise Exception

        # field type
        if (field_dict['type'] == 'freq'):
          if ('freq_file' not in field_dict):
            print('Error: Field of type "freq" has no file name given')
            raise Exception
        elif (field_dict['type'] == 'date'):
          if (not ('start_date' in field_dict and 'end_date' in field_dict)):
            print('Error: Field of type "date" has no start and/or end date given')
            raise Exception

          else:  # Process start and end date
            start_date = field_dict['start_date']
            end_date =   field_dict['end_date']

            start_epoch = utils.date_to_epoch(start_date[0], start_date[1], start_date[2])
            end_epoch =   utils.date_to_epoch(end_date[0], end_date[1], end_date[2])
            field_dict['start_epoch'] = start_epoch
            field_dict['end_epoch'] =   end_epoch
            cf.field_list[i] = field_dict

        elif (field_dict['type'] == 'phone'):
          if (not ('area_codes' in field_dict and 'num_digits' in field_dict)):
            print('Error: Field of type "phone" has no area codes and/or number ' + 'of digits given')
            raise Exception

          else:  # Process area codes and number of digits
            if (isinstance(field_dict['area_codes'],str)):  # Only one area code
              field_dict['area_codes'] = [field_dict['area_codes']]  # Make it a list
            if (not isinstance(field_dict['area_codes'],list)):
              print('Error: Area codes given are not a string or a list: %s' % \
                    (str(field_dict['area_codes'])))
              raise Exception

            if (not isinstance(field_dict['num_digits'],int)):
              print('Error: Number of digits given is not an integer: %s (%s)' % \
                    (str(field_dict['num_digits']), type(field_dict['num_digits'])))
              raise Exception

            cf.field_list[i] = field_dict

        elif (field_dict['type'] == 'ident'):
          if (not ('start_id' in field_dict and \
                  'end_id' in field_dict)):
            print('Error: Field of type "iden" has no start and/or end ' + \
                  'identification number given')
            raise Exception

        # Check all the probabilities for this field
        if ('select_prob' not in field_dict):
          field_dict['select_dict'] = 0.0
        elif (field_dict['select_prob'] < 0.0) or (field_dict['select_prob'] > 1.0):
          print('Error: Illegal value for select probability in dictionary for '+'field "%s": %f' % (field_dict['name'], field_dict['select_prob']))
        else:
          select_prob_sum += field_dict['select_prob']

        field_prob_sum = 0.0

        for prob in prob_names:
          if (prob not in field_dict):
            field_dict[prob] = 0.0
          elif (field_dict[prob] < 0.0) or (field_dict[prob] > 1.0):
            print('Error: Illegal value for "%s" probability in dictionary for ' % (prob) + 'field "%s": %f' % (field_dict['name'], field_dict[prob]))
            raise Exception
          else:
            field_prob_sum += field_dict[prob]

        if (field_prob_sum > 0.0) and (abs(field_prob_sum - 1.0) > 0.001):
            print('Error: Sum of probabilities for field "%s" is not 1.0: %f' % \
                  (field_dict['name'], field_prob_sum))
            raise Exception

        # Create a list of field probabilities and insert into field dictionary
        #
        prob_list = []
        prob_sum =  0.0

        for prob in prob_names:
          prob_list.append((prob, prob_sum))
          prob_sum += field_dict[prob]

        field_dict['prob_list'] = prob_list
        cf.field_list[i] = field_dict  # Store dictionary back into dictionary list

        i += 1
      # end of  fields dictionnaries validation
      
      
      if (abs(select_prob_sum - 1.0) > 0.001):
        print('Error: Field select probabilities do not sum to 1.0: %f' % (select_prob_sum))
        raise Exception
      
      return select_prob_sum
    
  def _duplicate_distribution(self):
      """ Create a distribution for the number of duplicates for an original record """
  
      num_dup =  1
      prob_sum = 0.0
      prob_dist_list = [(num_dup, prob_sum)]
      
      if (self.prob_distribution == 'uni'):  # Uniform distribution of duplicates - - - -

        uniform_val = 1.0 / float(self.max_num_dups)

        for i in range(self.max_num_dups-1):
          num_dup += 1
          prob_dist_list.append((num_dup, uniform_val+prob_dist_list[-1][1]))

      elif (self.prob_distribution == 'poi'):  # Poisson distribution of duplicates - - -

        def fac(n):  # Factorial of an integer number (recursive calculation)
          if (n > 1.0):
            return n*fac(n - 1.0)
          else:
            return 1.0

        poisson_num = []   # A list of poisson numbers
        poisson_sum = 0.0  # The sum of all poisson number

        # The mean (lambda) for the poisson numbers
        #
        mean = 1.0 + (float(self.num_dup_records) / float(self.num_org_records))

        for i in range(self.max_num_dups):
          poisson_num.append((math.exp(-mean) * (mean ** i)) / fac(i))
          poisson_sum += poisson_num[-1]

        for i in range(self.max_num_dups):  # Scale so they sum up to 1.0
          poisson_num[i] = poisson_num[i] / poisson_sum

        for i in range(self.max_num_dups-1):
          num_dup += 1
          prob_dist_list.append((num_dup, poisson_num[i]+prob_dist_list[-1][1]))

      elif (self.prob_distribution == 'zip'):  # Zipf distribution of duplicates - - - - -
        zipf_theta = 0.5

        denom = 0.0
        for i in range(self.num_org_records):
          denom += (1.0 / (i+1) ** (1.0 - zipf_theta))

        zipf_c = 1.0 / denom
        zipf_num = []  # A list of Zipf numbers
        zipf_sum = 0.0  # The sum of all Zipf number

        for i in range(self.max_num_dups):
          zipf_num.append(zipf_c / ((i+1) ** (1.0 - zipf_theta)))
          zipf_sum += zipf_num[-1]

        for i in range(self.max_num_dups):  # Scale so they sum up to 1.0
          zipf_num[i] = zipf_num[i] / zipf_sum

        for i in range(self.max_num_dups-1):
          num_dup += 1
          prob_dist_list.append((num_dup, zipf_num[i]+prob_dist_list[-1][1]))

      print()
      print('Create %i original and %i duplicate records' % (self.num_org_records, self.num_dup_records))
      print('  Distribution of number of duplicates (maximal %i duplicates):' % (self.max_num_dups))
      print('  %s' % (prob_dist_list))
      
      return prob_dist_list
 
  def _set_distribution(self, min_bound, max_bound, type_distrib):
    """ Set a distribution for family age gaps """
      
    num_dup =  1
    prob_sum = 0.0
    prob_dist_list = [(num_dup, prob_sum)]
    num_dup_records_distrib = max_bound
    num_org_records_distrib = max_bound

    gap = max_bound-min_bound

    self.prob_distribution = type_distrib
    max_num_dups_distrib = gap

    if (self.prob_distribution == 'uni'):  # Uniform distribution

      uniform_val = 1.0 / float(max_num_dups_distrib)

      for i in range(max_num_dups_distrib-1):
        num_dup += 1
        prob_dist_list.append((num_dup, uniform_val+prob_dist_list[-1][1]))

    elif (self.prob_distribution == 'poi'):  # Poisson distribution

      def fac(n):  # Factorial of an integer number (recursive calculation)
        if (n > 1.0):
          return n*fac(n - 1.0)
        else:
          return 1.0

      poisson_num = []  # A list of poisson numbers
      poisson_sum = 0.0  # The sum of all poisson number

      # The mean (lambda) for the poisson numbers
      #
      mean = 1.0+(float(num_dup_records_distrib)/float(num_org_records_distrib))

      for i in range(max_num_dups_distrib):
        poisson_num.append((math.exp(-mean) * (mean ** i)) / fac(i))
        poisson_sum += poisson_num[-1]

      for i in range(max_num_dups_distrib):  # Scale so they sum up to 1.0
        poisson_num[i] = poisson_num[i] / poisson_sum

      for i in range(max_num_dups_distrib-1):
        num_dup += 1
        prob_dist_list.append((num_dup, poisson_num[i]+prob_dist_list[-1][1]))

    elif (self.prob_distribution == 'zip'):  # Zipf distribution
      zipf_theta = 0.5

      denom = 0.0
      for i in range(num_org_records_distrib):
        denom += (1.0 / (i+1) ** (1.0 - zipf_theta))

      zipf_c = 1.0 / denom
      zipf_num = []   # A list of Zipf numbers
      zipf_sum = 0.0  # The sum of all Zipf number

      for i in range(max_num_dups_distrib):
        zipf_num.append(zipf_c / ((i+1) ** (1.0 - zipf_theta)))
        zipf_sum += zipf_num[-1]

      for i in range(max_num_dups_distrib):  # Scale so they sum up to 1.0
        zipf_num[i] = zipf_num[i] / zipf_sum

      for i in range(max_num_dups_distrib-1):
        num_dup += 1
        prob_dist_list.append((num_dup, zipf_num[i]+prob_dist_list[-1][1]))

    return prob_dist_list
    
  def _load_frequency_lookup_tables(self):
    """ Load frequency files and misspellings dictionaries """
      
    freq_files = {}
    freq_files_length = {}

    i = 0  # Loop counter
    # import freq file , misspell file and lookup file
    for field_dict in cf.field_list:
      field_name = field_dict['name']

      # import freq file, shuffle data and return data in a list
      if (field_dict['type'] == 'freq'):  # Check for 'freq' field type

        file_name = field_dict['freq_file']  # Get the corresponding file name   
        if (file_name != None):
          try:
            fin = open(file_name)  # Open file for reading
          except:
            print('  Error: Can not open frequency file %s' % (file_name))
            raise Exception
          value_list = []  # List with all values of the frequency file

          for line in fin:
            line = line.strip()
            line_list = line.split(',')
            if (len(line_list) != 2):
              print('  Error: Illegal format in  frequency file %s: %s' % (file_name, line))
              raise Exception

            line_val =  line_list[0].strip()
            line_freq = int(line_list[1])

            # Append value as many times as given in frequency file
            #
            new_list = [line_val]* line_freq
            value_list += new_list

          random.shuffle(value_list)  # Randomly shuffle the list of values

          freq_files[field_name] = value_list
          freq_files_length[field_name] = len(value_list)

          if (VERBOSE_OUTPUT == True):
            print('  Loaded frequency file for field "%s" from file: %s' % \
                  (field_dict['name'], file_name))
            print()

        else:
          print('  Error: No file name defined for frequency field "%s"' % \
                (field_dict['name']))
          raise Exception
        # end of freg files
      
      
      # import misspell file,  return a dict
      if ('misspell_file' in field_dict):  # Load misspellings dictionary file
        misspell_file_name = field_dict['misspell_file']
        field_dict['misspell_dict'] = utils.load_misspellings_dict(misspell_file_name)

        if (VERBOSE_OUTPUT == True):
          print('  Loaded misspellings dictionary for field "%s" from file: "%s' \
                % (field_dict['name'], misspell_file_name))
          print()

      # import lookup_file,  and return data lookup dict
      if ('lookup_file' in field_dict):  # Load lookup dictionary file
        lookup_file_name = field_dict['lookup_file']
        field_dict['lookup_dict'] = utils.load_lookup_dict(lookup_file_name)

        if (VERBOSE_OUTPUT == True):
          print('  Loaded lookup dictionary for field "%s" from file: "%s' \
                % (field_dict['name'], lookup_file_name))
          print()

        cf.field_list[i] = field_dict  # Store dictionary back into dictionary list

      i += 1

    # -----------------------------------------------------------------------------
    # Load frequency files for household age distribution
    #
    for field in cf.household_freq_dict:
      try:
        fin = open(cf.household_freq_dict[field])  # Open file for reading
      except:
        print('  Error: Can not open household frequency file %s' % (household_freq_dict[field]))
        raise Exception

      value_list = []  # List with all values of the frequency file

      for line in fin:
        line = line.strip()
        line_list = line.split(',')
        if (len(line_list) != 2):
          print(' Error: Illegal format in  frequency file %s: %s' % (household_freq_dict[field], line))
          raise Exception

        line_val =  line_list[0].strip()
        line_freq = int(line_list[1])

        # Append value as many times as given in frequency file
        #
        new_list = [line_val]* line_freq
        value_list += new_list

      random.shuffle(value_list)  # Randomly shuffle the list of values

      freq_files['household_'+field] = value_list
      freq_files_length['household_'+field] = len(value_list)

    
    return freq_files, freq_files_length
   
  def _create_original_records(self,freq_files_length,freq_files,all_rec_set):
    """ Create original records' """
    
    org_rec = {}  # Dictionary for original records
    rec_cnt = 0

    #Loop to create orginal records
    while (rec_cnt < self.num_org_records):
      rec_id = 'rec-%i-org' % (rec_cnt)  # The records identifier

      rec_dict = {'rec_id':rec_id}  # Save record identifier

      # Now randomly create all the fields in a record  - - - - - - - - - - - - - -
      #
      for field_dict in cf.field_list:
        field_name = field_dict['name']
        
       
        if ((field_name != 'culture') & (random.random() <= field_dict['miss_prob'])):
          rand_val = cf.missing_value

        elif (field_dict['type'] == 'freq'):  # A frequency file based field

          if(field_name == 'culture') :
            rand_val = 'uga'
          else:
            rand_num = random.randint(0, freq_files_length[field_name]-1)
            rand_val = freq_files[field_name][rand_num]

          # Check for dependencies and follow if a certain probability is given
          #
          if (('depend' in field_dict) and (random.random() <= field_dict['depend_prob'])):

            depend_field = field_dict['depend']  # The field this field depends on

            if (',' not in depend_field):  # A single dependency field
              if (depend_field in rec_dict):  # Randomly select a depdendent value

                # Get the value from the current record in the dependency field
                #
                depend_value = rec_dict[depend_field].replace(' ','')
                if (depend_value in field_dict['lookup_dict']):
                  rand_val = random.choice(field_dict['lookup_dict'][depend_value])

            else:  # Several fields this field depends upon
              depend_field_list = depend_field.split(',')
              depend_value_list = []
              depend_value = ''
              for df in depend_field_list:  # Create the dependency value
                if (df in rec_dict):
                  df = df.replace(' ', '')
                  depend_value_list.append(rec_dict[df])
                  #depend_value += '-' + rec_dict[df]
              depend_value = '-'.join(depend_value_list)
              if (depend_value in field_dict['lookup_dict']):
                rand_val = random.choice(field_dict['lookup_dict'][depend_value])
                print('XX: got combined dependency value: %s' % (rand_val), depend_field, depend_value)  
                #####################

        elif (field_dict['type'] == 'date'):  # A date field

          rand_num = random.randint(field_dict['start_epoch'], field_dict['end_epoch']-1)
          rand_date = utils.epoch_to_date(rand_num) # Date triuplet
          rand_val = rand_date[2]+rand_date[1]+rand_date[0]  # ISO format: yyyymmdd

          # Check for dependencies and follow if a certain probability is given
          #
          if ((field_dict['name'] == 'date_of_birth') and \
              (random.random() < field_dict['depend_prob']) and \
              (rec_dict.get('age', None) != None)):

            # Replace year with the year according to the 'age' field value
            #
            assert ' ' not in rec_dict['age'], rec_dict['age']
            assert rec_dict['age'] != '', 'Empty "rec_dict[age]"'

            year_birth = cf.current_year-int(rec_dict['age'])
            rand_val   = str(year_birth)+rand_date[1]+rand_date[0] # ISO format

            # With a certain probability modify the age value (break dependency)
            #
            if (random.random() > cf.age_dict['depend_prob']):
              rand_num = random.randint(0, freq_files_length['age']-1)
              rec_dict['age'] = freq_files['age'][rand_num]

              print('XX:  randomly replaced age:', rec_dict) #################

        elif (field_dict['type'] == 'phone'):  # A phone number field

          area_code = random.choice(field_dict['area_codes'])

          # Check for dependencies and follow if a certain probability is given
          #
          if (('depend' in field_dict) and   (random.random() <= field_dict['depend_prob'])):

            depend_field = field_dict['depend']

            if (depend_field in rec_dict):
              depend_value = rec_dict[depend_field]
              depend_value = depend_value.replace(' ', '')
              if (depend_value in field_dict['lookup_dict']):
                area_code = random.choice(field_dict['lookup_dict'][depend_value])

          max_digit = int('9'*field_dict['num_digits'])
          min_digit = int('1'*(int(1+round(field_dict['num_digits']/2.))))
          rand_num = random.randint(min_digit, max_digit)
          rand_val = area_code+' '+str(rand_num).zfill(field_dict['num_digits'])

        elif (field_dict['type'] == 'ident'):  # A identification number field
          rand_num = random.randint(field_dict['start_id'], field_dict['end_id']-1)
          rand_val = str(rand_num)
          
          if(field_dict['name']=='soc_sec_id'):
            # generate random 4 letters for Uganda NIN
            rand_uganda = ''.join([random.choice(string.ascii_letters) for n in range(4)]).lower()
            rand_val = str(rand_num) + rand_uganda

        elif (field_dict['type'] == 'others'):
          rand_val = 'NoRole'

        # Save value into record dictionary
        #
        if (rand_val != cf.missing_value):  # Don't save missing values
          rec_dict[field_name] = rand_val

      #### end of random field value assignation
      
      # Create a string representation which can be used to check for uniqueness
      #
      rec_data = rec_dict.copy()  # Make a copy of the record dictionary
      del(rec_data['rec_id'])     # Remove the record identifier
      rec_list = list(rec_data.items())
      rec_list.sort()
      rec_str = str(rec_list)

      if (rec_str not in all_rec_set):  # Check if same record already created
        all_rec_set.add(rec_str)
        org_rec[rec_id] = rec_dict  # Insert into original records
        rec_cnt += 1

        # Print original record - - - - - - - - - - - - - - - - - - - - - - - - - -
        #
        if (VERBOSE_OUTPUT == True):
          print('  Original:')
          print('    Record ID         : %-30s' % (rec_dict['rec_id']))
          for field_name in self.field_names:
            print('    %-18s: %-30s' % (field_name, rec_dict.get(field_name, cf.missing_value)))
          print()

      else:
        if (VERBOSE_OUTPUT == True):
          print('***** Record "%s" already created' % (rec_str))
    # end of loop for orinal records

    return org_rec
   
  def _create_households_familiy_records(self,freq_files,freq_files_length,org_rec):
    """ Create households family records """
          
    if (self.num_of_hofam_duplicate > 0):

      dup_hofam_rec = {}       # Dictionary for duplicate records
      org_hofam_rec_used = {}  # Dictionary with record IDs of original records
                              # used to create duplicates

      rec_cnt = 0  # Counter for number of records to be generated

      # List of household/familiy values to be used when coosing type
      #
      hf_list = ['h']*int(household_prob*100) + ['f']*int(family_prob*100)

      while (rec_cnt < self.num_of_hofam_duplicate):

        # Randomly select either to generate a familiy or household
        #
        if (random.choice(hf_list) == 'f'):
          family_flag = True
          min_age = -1 # Means no minimum age
        else:
          family_flag = False
          min_age = 17  # For people living in shared households

        rec_age = 0

        # Randomly select a record that so far has not been used
        #
        all_fields_flag = False  # Check that all fields are in the original record
        rand_rec_num = random.randint(0, self.num_org_records-1)
        org_rec_id = 'rec-%i-org' % (rand_rec_num)

        while ((org_rec_id in org_hofam_rec_used) or \
              (org_rec_id not in org_rec) or (rec_age < min_age) or \
              (all_fields_flag == False)):

          # Try another record
          #
          rand_rec_num = random.randint(0, self.num_org_records-1)
          org_rec_id = 'rec-%i-org' % (rand_rec_num)

          org_rec_dict = org_rec[org_rec_id]
          rec_age = int(org_rec_dict.get('age', 0))

          all_fields_flag = True
          for field_dict in cf.field_list:
            if (field_dict['name'] not in org_rec_dict):
              all_fields_flag = False
              break

        org_rec_dict = org_rec[org_rec_id]  # Get the original record

        # Generate the original (first) record in the family or household - - - - -
        #
        age = int(org_rec_dict['age'])
        sex = org_rec_dict['sex']
        family_culture = org_rec_dict['culture']
        year_of_birth = int(org_rec_dict['date_of_birth'][0:4])

        assert ' ' not in sex, sex
        assert ' ' not in family_culture, family_culture

        # Some information about what will be changed and what is kept for families
        # and households:
        #
        # Family
        # change: given_name, date_of_birth, age, soc_sec_id, blocking_number
        # keep:   surname, street_number, address_1, address_2, suburb, postcode,
        #         state, phone_number
        #
        # Decide who is the selected record (husband, wife, son, daughter) and
        # his/her culture by checking sex and age
        # male, husband/son
        # female, wife/daughter
        #
        # Household
        # change: given_name, surname, date_of_birth, age, soc_sec_id,
        #         blocking_number
        # keep:   street_number, address_1, address_2, suburb, postcode, state,
        #         phone_number

        # Randomly choose how many duplicates to create from this record
        #
        num_dups = utils.random_select(prob_dist_list)

    ## PC 15/12 OK above #######################

        if (family_flag == True):

          age_min_move = 18

          prob_has_children = {'parent_has_children_0_16':0,
                              'parent_has_children_17_20':0.5,
                              'parent_has_children_21_25':0.8,
                              'parent_has_children_26_30':0.8,
                              'parent_has_children_31_40':0.8,
                              'parent_has_children_41_50':0.8,
                              'parent_has_children_51_60':0.8,
                              'parent_has_children_more_60':0.8}

          prob_create_role = {'husband':0.25,
                                'wife':0.25,
                                  'son':0.25,
                            'daughter':0.25,
                              'father':0.25,
                              'mother':0.25,
                              'brother':0.25,
                              'sister':0.25}

          prob_live_family = {'husband_with_wife_0_16':0.9,
                          'husband_with_wife_17_20':0.9,
                          'husband_with_wife_21_25':0.9,
                          'husband_with_wife_26_30':0.9,
                          'husband_with_wife_31_40':0.9,
                          'husband_with_wife_41_50':0.9,
                          'husband_with_wife_51_60':0.9,
                          'husband_with_wife_more_60':0.9,
                          'wife_with_husband_0_16':0.9,
                          'wife_with_husband_17_20':0.9,
                          'wife_with_husband_21_25':0.9,
                          'wife_with_husband_26_30':0.9,
                          'wife_with_husband_31_40':0.9,
                          'wife_with_husband_41_50':0.9,
                          'wife_with_husband_51_60':0.9,
                          'wife_with_husband_more_60':0.9,
                          'parent_with_children_0_16':0,
                          'parent_with_children_17_20':0.9,
                          'parent_with_children_21_25':0.9,
                          'parent_with_children_26_30':0.9,
                          'parent_with_children_31_40':0.8,
                          'parent_with_children_41_50':0.8,
                          'parent_with_children_51_60':0.7,
                          'parent_with_children_more_60':0.5,
                                'father_with_son_0_16':0,
                                'father_with_son_17_20':0.95,
                                'father_with_son_21_25':0.9,
                                'father_with_son_26_30':0.9,
                                'father_with_son_31_40':0.9,
                                'father_with_son_41_50':0.8,
                                'father_with_son_51_60':0.7,
                                'father_with_son_more_60':0.5,
                          'father_with_daughter_0_16':0,
                          'father_with_daughter_17_20':0.95,
                          'father_with_daughter_21_25':0.9,
                          'father_with_daughter_26_30':0.9,
                          'father_with_daughter_31_40':0.9,
                          'father_with_daughter_41_50':0.8,
                          'father_with_daughter_51_60':0.7,
                          'father_with_daughter_more_60':0.5,
                                'mother_with_son_0_16':0,
                                'mother_with_son_17_20':0.95,
                                'mother_with_son_21_25':0.9,
                                'mother_with_son_26_30':0.9,
                                'mother_with_son_31_40':0.9,
                                'mother_with_son_41_50':0.8,
                                'mother_with_son_51_60':0.7,
                                'mother_with_son_more_60':0.5,
                          'mother_with_daughter_0_16':0,
                          'mother_with_daughter_17_20':0.95,
                          'mother_with_daughter_21_25':0.9,
                          'mother_with_daughter_26_30':0.9,
                          'mother_with_daughter_31_40':0.9,
                          'mother_with_daughter_41_50':0.8,
                          'mother_with_daughter_51_60':0.7,
                          'mother_with_daughter_more_60':0.5,
                          'son_with_father_0_16':1,
                          'son_with_father_17_20':0.3,
                          'son_with_father_21_25':0.3,
                          'son_with_father_26_30':0.3,
                          'son_with_father_31_40':0.1,
                          'son_with_father_41_50':0.01,
                          'son_with_father_51_60':0.01,
                          'son_with_father_more_60':0.01,
                          'son_with_mother_0_16':1,
                          'son_with_mother_17_20':0.3,
                          'son_with_mother_21_25':0.3,
                          'son_with_mother_26_30':0.3,
                          'son_with_mother_31_40':0.1,
                          'son_with_mother_41_50':0.01,
                          'son_with_mother_51_60':0.01,
                          'son_with_mother_more_60':0.01,
                          'daughter_with_father_0_16':1,
                          'daughter_with_father_17_20':0.7,
                          'daughter_with_father_21_25':0.6,
                          'daughter_with_father_26_30':0.4,
                          'daughter_with_father_31_40':0.2,
                          'daughter_with_father_41_50':0.1,
                          'daughter_with_father_51_60':0.01,
                          'daughter_with_father_more_60':0.01,
                          'daughter_with_mother_0_16':1,
                          'daughter_with_mother_17_20':0.7,
                          'daughter_with_mother_21_25':0.6,
                          'daughter_with_mother_26_30':0.4,
                          'daughter_with_mother_31_40':0.2,
                          'daughter_with_mother_41_50':0.1,
                          'daughter_with_mother_51_60':0.01,
                          'daughter_with_mother_more_60':0.01,
                          'brother_with_brother_0_16':0.9,
                          'brother_with_brother_17_20':0.9,
                          'brother_with_brother_21_25':0.8,
                          'brother_with_brother_26_30':0.4,
                          'brother_with_brother_31_40':0.04,
                          'brother_with_brother_41_50':0.03,
                          'brother_with_brother_51_60':0.02,
                          'brother_with_brother_more_60':0.01,
                          'brother_with_sister_0_16':0.9,
                          'brother_with_sister_17_20':0.9,
                          'brother_with_sister_21_25':0.8,
                          'brother_with_sister_26_30':0.4,
                          'brother_with_sister_31_40':0.04,
                          'brother_with_sister_41_50':0.03,
                          'brother_with_sister_51_60':0.02,
                          'brother_with_sister_more_60':0.01,
                          'sister_with_sister_0_16':0.9,
                          'sister_with_sister_17_20':0.9,
                          'sister_with_sister_21_25':0.8,
                          'sister_with_sister_26_30':0.4,
                          'sister_with_sister_31_40':0.04,
                          'sister_with_sister_41_50':0.03,
                          'sister_with_sister_51_60':0.02,
                          'sister_with_sister_more_60':0.01,
                          'sister_with_brother_0_16':0.9,
                          'sister_with_brother_17_20':0.9,
                          'sister_with_brother_21_25':0.8,
                          'sister_with_brother_26_30':0.4,
                          'sister_with_brother_31_40':0.04,
                          'sister_with_brother_41_50':0.03,
                          'sister_with_brother_51_60':0.02,
                        'sister_with_brother_more_60':0.01}

          num_roles_family = {'husband':0,
                            'wife':0,
                                  'son':0,
                            'daughter':0,
                              'father':0,
                              'mother':0,
                              'brother':0,
                              'sister':0}

          family_role_to_create = []
          family_role_to_create_live = []

          age_gap = {'min_husband_with_wife':0,
                    'max_husband_with_wife':20,
                    'min_father_with_children':16,
                    'max_father_with_children':40,
                    'min_mother_with_children':16,
                    'max_mother_with_children':40,
                    'min_sibling':1,
                    'max_sibling':5}

          prob_distribution_age_gap = 'uni' # uni,poi,zip

          prob_first = {'daughter':0.5,
                            'son':0.5,
                        'brother':0.5,
                          'sister':0.5}

          # +(older) (-)younger
          prob_age_gap = {'+' : 0.5,
                          '-' : 0.5}

          family_age_gap = []
          family_age_gap_sign = []

          prob_age_roles = {'husband_0_16':0,
                            'husband_17_20':0.2,
                            'husband_21_25':0.5,
                            'husband_26_30':0.6,
                            'husband_31_40':0.75,
                            'husband_41_50':0.8,
                            'husband_51_60':0.9,
                            'husband_more_60':0.95,
                            'son_0_16':1,
                            'son_17_20':0.8,
                            'son_21_25':0,
                            'son_26_30':0,
                            'son_31_40':0,
                            'son_41_50':0,
                            'son_51_60':0,
                            'son_more_60':0,
                            'wife_0_16':0,
                            'wife_17_20':0.2,
                            'wife_21_25':0.5,
                            'wife_26_30':0.6,
                            'wife_31_40':0.75,
                            'wife_41_50':0.8,
                            'wife_51_60':0.9,
                            'wife_more_60':0.95,
                            'daughter_0_16':1,
                            'daughter_17_20':0.8,
                            'daughter_21_25':0,
                            'daughter_26_30':0,
                            'daughter_31_40':0,
                            'daughter_41_50':0,
                            'daughter_51_60':0,
                            'daughter_more_60':0}

          family_role_male_list=[]
          family_role_female_list=[]

          str_key = ''
          if (age >= 0) and (age <=16):
            str_key='_0_16'
          elif (age >= 17) and (age <=20):
            str_key='_17_20'
          elif (age >= 21) and (age <=25):
            str_key='_21_25'
          elif (age >= 26) and (age <=30):
            str_key='_26_30'
          elif (age >= 31) and (age <=40):
            str_key='_31_40'
          elif (age >= 41) and (age <=50):
            str_key='_41_50'
          elif (age >= 51) and (age <=60):
            str_key='_51_60'
          elif (age>60):
            str_key='_more_60'

          # family role
          if (sex == 'm'):
            for i in range(int(prob_age_roles['husband'+str_key]*100)):
              family_role_male_list.insert (i,'husband')
            for j in range(int(prob_age_roles['son'+str_key]*100)):
              family_role_male_list.insert (i+j,'son')
            family_role = random.choice (family_role_male_list)

          if (sex == 'f'):
            for i in range(int(prob_age_roles['wife'+str_key]*100)):
              family_role_female_list.insert (i,'wife')
            for j in range(int(prob_age_roles['daughter'+str_key]*100)):
              family_role_female_list.insert (i+j,'daughter')
            family_role = random.choice (family_role_female_list)

          #
          list_create_son_daughter = []
          list_create_brother_sister = []

          for t in prob_first:
            if (t in ['son','daughter']):
              for i in range(int(prob_first[t]*100)):
                list_create_son_daughter.insert (i,t)
            else:
              for i in range(int(prob_first[t]*100)):
                list_create_brother_sister.insert (i,t)

          #
          list_age_gap = []
          for t in prob_age_gap:
            for i in range(int(prob_age_gap[t]*100)):
              list_age_gap.insert (i,t)

          max_num_of_children = num_dups

          # husband  may have 0/1 wife, 0/x son, 0/x daughter,
          # wife     may have 0/1 husband, 0/x son, 0/x daughter
          # son      may have 0/1 father, 0/1 mother, 0/x sister, 0/x brother
          # daughter may have 0/1 father, 0/1 mother, 0/x brother, 0/x sister

          numrole = 0

          if (num_dups > 0):

            if (family_role=='husband'):

              if (random.random() <= prob_create_role['wife']):
                num_roles_family['wife']=1
                family_role_to_create.insert (len(family_role_to_create),'wife')
                max_num_of_children = max_num_of_children-1

                if (random.random() <= prob_live_family['husband_with_wife' + \
                                                        str_key]):
                  family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'y')
                else:
                  family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'n')

              if ((random.random() <= prob_has_children['parent_has_children' + \
                  str_key]) and (max_num_of_children > 0)):

                while (numrole < max_num_of_children):
                  str_children= random.choice(list_create_son_daughter)

                  if (random.random() <=  prob_create_role[str_children]):
                    family_role_to_create.insert(len(family_role_to_create), \
                                                str_children)
                    numrole+=1

                    if (random.random()<=prob_live_family['parent_with_children' \
                                                          + str_key]):
                      family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'y')
                    else:
                      family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'n')

            elif (family_role=='wife'):
              if (random.random() <= prob_create_role['husband']):
                num_roles_family['husband'] = 1
                family_role_to_create.insert(len(family_role_to_create),'husband')
                max_num_of_children = num_dups-1

                if (random.random() <= prob_live_family['wife_with_husband' + \
                                                        str_key]):
                  family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'y')
                else:
                  family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'n')

              if ((random.random() <= prob_has_children['parent_has_children' + \
                                                        str_key]) and \
                  (max_num_of_children > 0)):

                while (numrole < max_num_of_children):

                  str_children= random.choice(list_create_son_daughter)

                  if (random.random() <= prob_create_role[str_children]):
                    family_role_to_create.insert(len(family_role_to_create), \
                                                str_children)
                    numrole+=1

                    if (random.random() <=prob_live_family['parent_with_children' \
                                                          + str_key]):
                      family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'y')
                    else:
                      family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'n')

            elif (family_role in ['son']):
              if (random.random() <= prob_create_role['father']):
                num_roles_family['father'] = 1
                family_role_to_create.insert(len(family_role_to_create), 'father')
                max_num_of_children = num_dups-1

                if (random.random() <= prob_live_family['son_with_father' + \
                                                        str_key]):
                  family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'y')
                else:
                  family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'n')

              if (random.random() <= prob_create_role['mother']):
                num_roles_family['mother'] = 1
                family_role_to_create.insert (len(family_role_to_create),'mother')
                max_num_of_children = num_dups-1

                if (random.random() <= prob_live_family['son_with_mother' + \
                                                        str_key]):
                  family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'y')
                else:
                  family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'n')

              while (numrole < max_num_of_children):
                str_children= random.choice(list_create_brother_sister)
                if (random.random() <=  prob_create_role[str_children]):
                  family_role_to_create.insert(len(family_role_to_create), \
                                              str_children)
                  numrole += 1

                  if (random.random() <= prob_live_family['brother_with_' + \
                                                          str_children+str_key]):
                    family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'y')
                  else:
                    family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'n')

            elif (family_role in ['daughter']):
              if (random.random() <= prob_create_role['father']):
                num_roles_family['father'] = 1
                family_role_to_create.insert (len(family_role_to_create),'father')
                max_num_of_children = num_dups-1

                if (random.random() <= prob_live_family['daughter_with_father' + \
                                                        str_key]):
                  family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'y')
                else:
                  family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'n')

              if (random.random() <= prob_create_role['mother']):
                num_roles_family['mother'] = 1
                family_role_to_create.insert (len(family_role_to_create),'mother')
                max_num_of_children = num_dups-1

                if (random.random() <= prob_live_family['daughter_with_mother' + \
                                                        str_key]):
                  family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'y')
                else:
                  family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'n')

              while (numrole < max_num_of_children):
                str_children= random.choice(list_create_brother_sister)
                if (random.random() <= prob_create_role[str_children]):
                  family_role_to_create.insert(len(family_role_to_create), \
                                              str_children)
                  numrole += 1

                  if (random.random() <= prob_live_family[str_children + \
                                                          '_with_sister'+str_key]):
                    family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'y')
                  else:
                    family_role_to_create_live.insert( \
                                              len(family_role_to_create_live),'n')

            num_dups=len(family_role_to_create)

          family_age_rec={}

        # End family specific part

        dup_count = 0

        parent_address = {'state':'',
                        'suburb':'',
                      'postcode':'',
                  'street_number':'',
                      'address_1':'',
                      'address_2':'',
                  'phone_number':''}

        parent_father_address = {'state':'',
                                'suburb':'',
                              'postcode':'',
                        'street_number':'',
                            'address_1':'',
                            'address_2':'',
                          'phone_number':''}

        parent_mother_address = {'state':'',
                                'suburb':'',
                              'postcode':'',
                        'street_number':'',
                            'address_1':'',
                            'address_2':'',
                          'phone_number':''}

        parent_sibling_address = {'state':'',
                                'suburb':'',
                              'postcode':'',
                          'street_number':'',
                              'address_1':'',
                              'address_2':'',
                          'phone_number':''}

        # Now create the other records in the familiy or the household - - - - - -
        #
        while (dup_count < num_dups) and (rec_cnt < self.num_of_hofam_duplicate):

          # Create a duplicate of the original record
          #
          dup_rec_dict = org_rec_dict.copy()  # Make a copy of the original record

          if (family_flag == True):
            dup_rec_id =  'rec-%i-org_f-%i' % (rand_rec_num, dup_count)
          else:
            dup_rec_id =  'rec-%i-org_h-%i' % (rand_rec_num, dup_count)

          dup_rec_dict['rec_id'] = dup_rec_id

          num_modif_in_record = 0

          # Set the field modification counters to zero for all fields
          #
          field_mod_count_dict = {}

          for cf.field_dict in cf.field_list:
            field_mod_count_dict[field_dict['name']] = 0

          if (family_flag == True):

            if ((cf.field_name in parent_address) and \
                ('father' not in family_role_to_create) and \
                ('mother' not in family_role_to_create)):
              parent_sibling_address[field_name] = org_rec_dict[cf.field_name]

            father_mother_live_together_flag = False
            if (random.random() <= prob_live_family['wife_with_husband'+str_key]):
              father_mother_live_together_flag = True

          # Now randomly create all the fields in a record  - - - - - - - - - - - -
          #
          for field_dict in cf.field_list:
            field_name = field_dict['name']

            old_field_val = dup_rec_dict.get(field_name, None)
            dup_field_val = old_field_val  # Modify this value

            org_field_val = org_rec_dict.get(field_name, None) # Get original value

            # Randomly set field values to missing
            #
            if (dup_field_val != None):
              rand_val = dup_field_val.replace(blank_value,'')
            blank_flag=''
            if (random.random() <= field_dict['miss_prob']):
              blank_flag = blank_value


            field_filter = household_field_list
            if (family_flag == True):
              #default
              field_filter = family_field_list

              if ('age' in dup_rec_dict):
                age_value = int(dup_rec_dict['age'].replace(blank_value,''))

                str_key = ''
                if (age >= 0) and (age <=16):
                  str_key='_0_16'
                elif (age >= 17) and (age <=20):
                  str_key='_17_20'
                elif (age >= 21) and (age <=25):
                  str_key='_21_25'
                elif (age >= 26) and (age <=30):
                  str_key='_26_30'
                elif (age >= 31) and (age <=40):
                  str_key='_31_40'
                elif (age >= 41) and (age <=50):
                  str_key='_41_50'
                elif (age >= 51) and (age <=60):
                  str_key='_51_60'
                elif (age>60):
                  str_key='_more_60'

                if (family_role_to_create[dup_count] in \
                    ['son','daughter','brother','sister']):
                  #brother sister
                  if ((family_role_to_create[dup_count] in ['brother']) and \
                      (family_role in ['son'])):
                    str_key1='brother_with_'
                    str_key2='brother'
                    str_key3='son'
                  elif ((family_role_to_create[dup_count] in ['brother']) and \
                        (family_role in ['daughter'])):
                    str_key1='brother_with_'
                    str_key2='sister'
                    str_key3='son'

                  if ((family_role_to_create[dup_count] in ['sister']) and \
                      (family_role in ['son'])):
                    str_key1='sister_with_'
                    str_key2='brother'
                    str_key3='daughter'
                  elif ((family_role_to_create[dup_count] in ['sister']) and \
                        (family_role in ['daughter'])):
                    str_key1='sister_with_'
                    str_key2='sister'
                    str_key3='daughter'

                  if ((family_role_to_create[dup_count] in ['son','daughter']) \
                      and (family_role in ['husband','wife'])):
                    if (family_role in ['husband']):
                      str_key1='father'
                    elif (family_role in ['wife']):
                      str_key1='mother'

                  if (family_role_to_create[dup_count] in ['brother','sister']):
                    if ((age_value >= age_min_move) and (random.random() <= \
                        prob_live_family[str_key1+str_key2+str_key])):
                      family_role_to_create_live[dup_count] = 'n'
                    else:
                      family_role_to_create_live[dup_count] = 'y'

                  elif (family_role_to_create[dup_count] in ['son','daughter']):
                    if ((age_value >= age_min_move) and (random.random() <= \
                        prob_live_family[family_role_to_create[dup_count] + \
                        '_with_'+str_key1+str_key])):
                      family_role_to_create_live[dup_count] = 'n'
                    else:
                      family_role_to_create_live[dup_count] = 'y'

                  if ((family_role_to_create[dup_count] in ['son','daughter']) \
                      and (family_role_to_create_live[dup_count] == 'y')):
                    #son daughter
                    list_live_with1 = []
                    for i in range(int(prob_live_family[family_role_to_create[ \
                                  dup_count]+'_with_father'+str_key]*100)):
                      list_live_with1 += 'father'
                    for i in range(int(prob_live_family[family_role_to_create[ \
                                  dup_count]+'_with_mother'+str_key]*100)):
                      list_live_with1 += 'mother'
                    live_with = random.choice(list_live_with1)
                  elif ((family_role_to_create[dup_count] in ['brother','sister'])\
                        and (family_role in ['son','daughter']) and \
                        (family_role_to_create_live[dup_count] == 'y')):
                    list_live_with2 = []
                    for i in range(int(prob_live_family[str_key1+ \
                                                        str_key2+str_key]*100)):
                      list_live_with2 += 'sibling'
                    for i in range(int(prob_live_family[str_key3+ \
                                                    '_with_father'+str_key]*100)):
                      list_live_with2 += 'father'
                    for i in range(int(prob_live_family[str_key3+ \
                                                    '_with_mother'+str_key]*100)):
                      list_live_with2 += 'mother'
                    live_with = random.choice(list_live_with2)

              if (family_role_to_create_live[dup_count] in ['n']):
                field_filter = ['surname']

            if (field_name not in field_filter):
              if (field_dict['type'] == 'freq'):  # A frequency file based field

                #default value by freq
                #
                if (family_flag == False) and (field_name not in ['culture']):
                  str_key = ''
                  if (field_name in ['age','sex']):
                    str_key='household_'
                  rand_num = random.randint(0, freq_files_length[str_key+ \
                                                                field_name]-1)
                  rand_val = freq_files[str_key+field_name][rand_num]
                elif (family_flag == True):
                  rand_num = random.randint(0, freq_files_length[field_name]-1)
                  rand_val = freq_files[field_name][rand_num]

                if (family_flag == True):
                  if (field_name == 'culture'):
                    rand_val = family_culture
                  elif (field_name == 'sex'):
                    if family_role_to_create[dup_count] in \
                                              ['husband','father','son','brother']:
                      rand_val = 'm'
                    elif family_role_to_create[dup_count] in \
                                            ['wife','mother','daughter','sister']:
                      rand_val = 'f'
                  elif (field_name == 'age'):
                    if family_role_to_create[dup_count] in ['father','mother']:
                      if family_role_to_create[dup_count] in ['father']:
                        gap = utils.random_select(self._set_distribution(age_gap[ \
                                  'min_father_with_children'], \
                                  age_gap['max_father_with_children'], \
                                  prob_distribution_age_gap))+ \
                                  age_gap['min_father_with_children']
                      else:
                        gap = utils.random_select(self._set_distribution(age_gap[ \
                                  'min_mother_with_children'], \
                                  age_gap['max_mother_with_children'], \
                                  prob_distribution_age_gap))+ \
                                  age_gap['min_mother_with_children']
                      rand_val = str(int(age) + gap)
                      family_age_rec[family_role_to_create[dup_count]] = rand_val
                      family_age_gap_sign.insert (dup_count,'+')
                      family_age_gap.insert (dup_count,gap)

                    elif family_role_to_create[dup_count] in ['husband','wife']:
                      rand_val = -1
                      while (int(rand_val) < 17):  # Minimum age
                        sign_val = random.choice(list_age_gap)
                        gap = utils.random_select(self._set_distribution( \
                                  age_gap['min_husband_with_wife'], \
                                  age_gap['max_husband_with_wife'], \
                                  prob_distribution_age_gap))+ \
                                  age_gap['min_husband_with_wife']
                        if (sign_val=='+'):
                          rand_val = str(int(age) + gap)
                        else:
                          rand_val = str(int(age) - gap)

                      family_age_gap_sign.insert (dup_count,sign_val)
                      family_age_gap.insert (dup_count,gap)
                      family_age_rec [family_role_to_create[dup_count]] = rand_val

                    elif family_role_to_create[dup_count] in ['son','daughter']:
                      for fr in family_age_rec:
                        if ((int(age) > family_age_rec[fr]) and \
                            (fr in ['father','mother','husband','wife'])):
                          age=str(family_age_rec[fr])
                      rand_val = -1
                      while (int(rand_val) <= 0):
                        if (family_role in ['husband']):
                          gap = utils.random_select(self._set_distribution( \
                                  age_gap['min_father_with_children'], \
                                  age_gap['max_father_with_children'], \
                                  prob_distribution_age_gap))+ \
                                  age_gap['min_father_with_children']

                        elif (family_role in ['wife']):
                          gap = utils.random_select(self._set_distribution( \
                                  age_gap['min_mother_with_children'], \
                                  age_gap['max_mother_with_children'], \
                                  prob_distribution_age_gap))+ \
                                  age_gap['min_mother_with_children']
                        rand_val = str(int(age) - gap)

                      family_age_rec [family_role_to_create[dup_count]] = rand_val
                      family_age_gap.insert (dup_count,gap)
                      family_age_gap_sign.insert (dup_count,'-')

                    elif family_role_to_create[dup_count] in ['brother','sister']:
                      rand_val = -1
                      while (int(rand_val) <= 0):
                        sign_val = random.choice(list_age_gap)
                        gap = utils.random_select(self._set_distribution( \
                                  age_gap['min_sibling'], \
                                  age_gap['max_sibling'], \
                                  prob_distribution_age_gap))+ \
                                  age_gap['min_sibling']

                        if (sign_val=='-') and (gap > int(age)):
                          sign_val='+'
                        if (sign_val=='+'):
                          rand_val = str(int(age) + gap)
                        else:
                          rand_val = str(int(age) - gap)

                      family_age_gap_sign.insert (dup_count,sign_val)
                      family_age_gap.insert (dup_count,gap)
                      family_age_rec [family_role_to_create[dup_count]] = rand_val

                if (family_flag == True):

                  if ((family_role_to_create[dup_count] in ['son','daughter']) \
                      and (family_role_to_create_live[dup_count] == 'y')):
                    if ((father_mother_live_together_flag) and \
                        (('husband' in family_role_to_create) and \
                        ('wife' in family_role_to_create))):
                      parent_address = parent_father_address
                    else:
                      if (live_with == 'father'):
                        parent_address = parent_father_address
                      else:
                        parent_address=parent_mother_address
                  elif ((family_role_to_create[dup_count] in \
                        ['brother','sister']) and (family_role in \
                        ['son','daughter']) and \
                        (family_role_to_create_live[dup_count] == 'y')):
                    if ((father_mother_live_together_flag) and \
                        (('father' in family_role_to_create) and \
                        ('mother' in family_role_to_create))):
                      parent_address = parent_father_address
                    else:
                      if ((live_with == 'father') and \
                          ('father' in family_role_to_create)):
                        parent_address = parent_father_address
                      elif ((live_with == 'mother') and \
                            ('mother' in family_role_to_create)):
                        parent_address = parent_mother_address
                      else:
                        parent_address = parent_sibling_address
                  elif ((family_role_to_create[dup_count] in ['mother']) and \
                        (family_role_to_create_live[dup_count] == 'y')):
                    if ((father_mother_live_together_flag) and \
                        (('father' in family_role_to_create) and \
                        ('mother' in family_role_to_create))):
                      parent_address = parent_father_address
                    else:
                      if ('father' in family_role_to_create):
                        parent_address = parent_father_address
                      else:
                        parent_address = parent_mother_address

                  elif ((family_role_to_create[dup_count] in ['wife']) and \
                        (family_role_to_create_live[dup_count] == 'y')):
                    if ((father_mother_live_together_flag) and \
                        (('husband' in family_role_to_create) and \
                        ('wife' in family_role_to_create))):
                      parent_address = parent_father_address
                    else:
                      if ('husband' in family_role_to_create):
                        parent_address = parent_father_address
                      else:
                        parent_address = parent_mother_address

                  do_depend=True
                  if ((field_name in parent_address) and \
                      (family_role_to_create[dup_count] in ['brother','sister']) \
                      and (family_role_to_create_live[dup_count] in ['y'])):
                    rand_val = parent_address[field_name]
                    do_depend = False
                  elif ((field_name in parent_address) and \
                        (family_role_to_create[dup_count] in ['mother']) and \
                        (family_role_to_create_live[dup_count] in ['n']) and \
                        ('father' in family_role_to_create) and \
                        father_mother_live_together_flag):
                    if (family_role_to_create_live[dup_count-1] in ['n']):
                      rand_val = parent_address[field_name]
                      do_depend = False
                else:
                  do_depend = True

                #Deal with dependencies
                #
                if (('depend' in field_dict) and (random.random() <= field_dict['depend_prob']) and (do_depend)):
                  depend_field = field_dict['depend']
                  if (depend_field.find(',') < 0):
                    if (depend_field in dup_rec_dict):
                      depend_value = dup_rec_dict[depend_field]
                      depend_value = depend_value.replace(blank_value,'').strip()
                      rand_val = random.choice(field_dict['lookup_dict'][depend_value])
                  else:
                    depend_field_list=depend_field.split(',')
                    depend_value = ''
                    for df in depend_field_list:
                      if (df in dup_rec_dict):
                        depend_value += '-' + dup_rec_dict[df]
                        depend_value = depend_value.replace(blank_value,'').strip()
                    depend_value = depend_value[1:]
                    depend_value = depend_value.replace(blank_value,'').strip()
                    if (depend_value in field_dict['lookup_dict']):
                      rand_val = random.choice(field_dict['lookup_dict'][depend_value])

              elif (field_dict['type'] == 'date'):  # A date field
                rand_num = random.randint(field_dict['start_epoch'],field_dict['end_epoch']-1)
                rand_date = utils.epoch_to_date(rand_num)
                rand_val = rand_date[2]+rand_date[1]+rand_date[0] # ISO format

                if (family_flag == False):
                  if ((field_dict['name']=='date_of_birth') and (random.random() < field_dict['depend_prob'])):
                    year_birth = cf.current_year - int(dup_rec_dict['age'].replace(blank_value,''))
                    rand_val   = str(year_birth)+rand_date[1]+rand_date[0]
                    if ((random.random() > cf.age_dict['depend_prob']) and (dup_rec_dict['age'].find(blank_value) < 0)):
                      rand_num = random.randint(0, freq_files_length['age']-1)
                      dup_rec_dict['age']= freq_files['age'][rand_num]

                if (family_flag == True):
                  if ((field_name == 'date_of_birth') and ('age' in rec_dict) and (random.random() < field_dict['depend_prob'])):
                    if (family_role_to_create[dup_count] in ['father','mother']):
                      rand_val = str(int(year_of_birth) -  int(family_age_gap[dup_count])) + rand_date[1]+rand_date[0]  # ISO format: yyyymmdd
                    elif (family_role_to_create[dup_count] in ['husband','wife']):
                      if (family_age_gap_sign[dup_count]=='+'):
                        rand_val = str(int(year_of_birth) + int(family_age_gap[dup_count])) + rand_date[1]+rand_date[0] # ISO format: yyyymmdd
                      else:
                        rand_val = str(int(year_of_birth) - int(family_age_gap[dup_count])) + rand_date[1]+rand_date[0] # ISO format: yyyymmdd
                    elif (family_role_to_create[dup_count] in ['son','daughter']):
                      rand_val = str(int(year_of_birth) +  int(family_age_gap[dup_count])) + rand_date[1]+rand_date[0]  # ISO format: yyyymmdd
                    elif (family_role_to_create[dup_count] in ['brother',
                                                              'sister']):
                      if (family_age_gap_sign[dup_count] == '+'):
                        rand_val = str(int(year_of_birth) + int(family_age_gap[dup_count])) + rand_date[1]+rand_date[0] # ISO format: yyyymmdd
                      else:
                        rand_val = str(int(year_of_birth) - int(family_age_gap[dup_count])) + rand_date[1]+rand_date[0] # ISO format: yyyymmdd
                    #
                    if ((random.random() > cf.age_dict['depend_prob']) and (dup_rec_dict['age'].find(blank_value)<0)):
                      rand_num = random.randint(0, freq_files_length['age']-1)
                      dup_rec_dict['age']= freq_files['age'][rand_num]

              elif (field_dict['type'] == 'phone'):  # A phone number field

                area_code = random.choice(field_dict['area_codes'])

                if (family_flag == True):

                  if ((family_role_to_create[dup_count] in ['son','daughter'])  and (family_role_to_create_live[dup_count] == 'y')):
                    if ((father_mother_live_together_flag) and  (('husband' in family_role_to_create) and ('wife' in family_role_to_create))):
                      parent_address = parent_father_address
                    else:
                      if (live_with == 'father'):
                        parent_address = parent_father_address
                      else:
                        parent_address = parent_mother_address
                  elif ((family_role_to_create[dup_count] in \
                        ['brother','sister']) and (family_role in \
                        ['son','daughter']) and \
                        (family_role_to_create_live[dup_count] == 'y')):
                    if ((father_mother_live_together_flag) and \
                        (('father' in family_role_to_create) and \
                        ('mother' in family_role_to_create))):
                      parent_address = parent_father_address
                    else:
                      if ((live_with == 'father') and \
                          ('father' in family_role_to_create)):
                        parent_address = parent_father_address
                      elif ((live_with == 'mother') and \
                            ('mother' in family_role_to_create)):
                        parent_address = parent_mother_address
                      else:
                        parent_address = parent_sibling_address
                  elif ((family_role_to_create[dup_count] in ['mother']) and \
                        (family_role_to_create_live[dup_count] == 'y')):
                    if ((father_mother_live_together_flag) and \
                        (('father' in family_role_to_create) and \
                        ('mother' in family_role_to_create))):
                      parent_address = parent_father_address
                    else:
                      if ('father' in family_role_to_create):
                        parent_address = parent_father_address
                      else:
                        parent_address = parent_mother_address

                  elif ((family_role_to_create[dup_count] in ['wife']) and \
                        (family_role_to_create_live[dup_count] == 'y')):
                    if ((father_mother_live_together_flag) and \
                        (('husband' in family_role_to_create) and \
                        ('wife' in family_role_to_create))):
                      parent_address = parent_father_address
                    else:
                      if ('husband' in family_role_to_create):
                        parent_address = parent_father_address
                      else:
                        parent_address = parent_mother_address

                  do_depend = True
                  if ((field_name in parent_address) and \
                      (family_role_to_create[dup_count] in ['brother','sister']) \
                      and (family_role_to_create_live[dup_count] in ['y'])):
                    rand_val = parent_address[field_name]
                    do_depend = False
                  elif ((field_name in parent_address) and \
                        (family_role_to_create[dup_count] in ['mother']) and \
                        (family_role_to_create_live[dup_count] in ['n']) and \
                        ('father' in family_role_to_create) and \
                        (father_mother_live_together_flag)):
                    if (family_role_to_create_live[dup_count-1] in ['n']):
                      rand_val = parent_address[field_name]
                      do_depend = False
                else:
                  do_depend=True

                # Deal with dependencies for areacode and state
                #
                if (('depend' in field_dict) and (random.random() <= \
                    field_dict['depend_prob']) and (do_depend)):
                  depend_field = field_dict['depend']

                  if (depend_field in rec_dict):
                    depend_value = rec_dict[depend_field]
                    depend_value = depend_value.replace(blank_value,'').strip()
                    area_code = random.choice(field_dict['lookup_dict'][ \
                                                                    depend_value])
                if (do_depend == True):
                  max_digit = int('9'*field_dict['num_digits'])
                  min_digit = int('1'*(int(1+round(field_dict['num_digits']/2.))))
                  rand_num = random.randint(min_digit, max_digit)
                  rand_val = area_code+' ' + \
                            str(rand_num).zfill(field_dict['num_digits'])

              elif (field_dict['type'] == 'ident'):  # Identification number field
                rand_num = random.randint(field_dict['start_id'], \
                                          field_dict['end_id']-1)
                rand_val = str(rand_num)

              elif (field_dict['type'] == 'others'):
                rand_val = 'NoRole'
                if (family_flag == True):
                  if (field_name == 'family_role'):
                    rand_val = family_role_to_create[dup_count] + '-' + \
                              family_role_to_create_live[dup_count] + '-' + \
                              str(father_mother_live_together_flag)

            dup_field_val = rand_val

            # Now check if the modified field value is different - - - - - - - - -
            #
            if (old_field_val == org_field_val) and \
              (dup_field_val != old_field_val):  # The first field modification
              field_mod_count_dict[field_name] = 1
              num_modif_in_record += 1
            elif ((old_field_val != org_field_val) and \
                  (dup_field_val != old_field_val)):  # Following modifications
              field_mod_count_dict[field_name] += 1
              num_modif_in_record += 1
            if ((dup_field_val != old_field_val) and \
                (field_name not in field_filter)) or (field_name in field_filter):
              dup_rec_dict[field_name] = dup_field_val + blank_flag

            if (family_flag == True):
              if (field_name in parent_address):
                if (family_role_to_create[dup_count] in ['father','husband']):
                  parent_father_address[field_name] = dup_field_val
                elif (((family_role_to_create[dup_count] in ['mother']) and \
                      ('father' not in family_role_to_create)) or \
                      ((family_role_to_create[dup_count] in ['wife']) and \
                      ('husband' not in family_role_to_create))):
                  parent_mother_address[field_name] = dup_field_val

          # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
          # Now check if the duplicate record differs from the original
          #
          rec_data = dup_rec_dict.copy()  # Make a copy of the record dictionary
          del(rec_data['rec_id'])         # Remove the record identifier
          rec_list = list(rec_data.items())
          rec_list.sort()
          rec_str = str(rec_list)
          if (rec_str not in all_rec_set):  # Check if same record already created
            all_rec_set.add(rec_str)

            # Insert into duplicate records
            #
            dup_hofam_rec[dup_rec_id] = dup_rec_dict

            dup_count += 1  # Duplicate counter (loop counter)

            if (family_flag == True):
              org_rec[org_rec_id]['family_role'] = 'Org-'+family_role

              if ((family_role in ['wife']) and \
                  (org_rec[org_rec_id]['title'].lower() in ['miss', 'ms'])):
                org_rec[org_rec_id]['title'] = 'mrs'

            else:  # Household
              org_rec[org_rec_id]['family_role'] ='Org-Household'

            org_hofam_rec_used[org_rec_id] = 1

            rec_cnt += 1

            # Print original and duplicate records field by field - - - - - - - - -
            #
            if (VERBOSE_OUTPUT == True):
              print('  Original and duplicate records:')
              print('    Number of modifications in record: %d' % \
                    (num_modif_in_record))
              print('    Record ID         : %-30s | %-30s' % \
                    (org_rec_dict['rec_id'], dup_rec_dict['rec_id']))
              for field_name in self.field_names:
                print('    %-18s: %-30s | %-30s' % (field_name, org_rec_dict.get(field_name, cf.missing_value), dup_rec_dict.get(field_name, cf.missing_value)))
            print()

          else:
            if (VERBOSE_OUTPUT == True):
              print('  No random modifications for record "%s" -> Choose another' % (dup_rec_id))

            if (VERBOSE_OUTPUT == True):
              print()

      # ---------------------------------------------------------------------------
      # Merge original and household and family records
      #
      new_org_rec = {}  # Dictionary for original records
      all_rec = org_rec
      all_rec.update(dup_hofam_rec)

      # Get all record IDs
      #
      all_rec_ids = list(all_rec.keys())

      # Loop over all record IDs
      #
      i = 0
      for rec_id in all_rec_ids:
        rec_dict = all_rec[rec_id]
        new_rec_id = 'rec-%i-org' % (i)
        rec_dict['rec2_id'] = rec_dict.get('rec_id')
        rec_dict['rec_id']  = new_rec_id
        new_org_rec[new_rec_id] = rec_dict
        i += 1
      self.num_org_records = i

    else:
      new_org_rec = org_rec

    ## PC 15/12 OK below #######################

    # -----------------------------------------------------------------------------
    
    return new_org_rec
    
  def _create_duplicate_records(self,
                                org_rec,
                                prob_dist_list,
                                new_org_rec,
                                select_prob_list,
                                all_rec_set,
                                freq_files_length,
                                freq_files):
    """  Create duplicate records """
    dup_rec = {}  # Dictionary for duplicate records

    org_rec_used = {}  # Dictionary with record IDs of original records used to
                        # create duplicates

    if (self.num_dup_records > 0):

     
      rec_cnt = 0  # Record counter

      while (rec_cnt < self.num_dup_records):

        if (self.type_modification=='all'):  # Randomly select an error type according
                                        # distribution given in parameter
                                        # 'error_type_distribution'
          list_type_of_error = []
          for error_type in cf.error_type_distribution:
            list_type_of_error += [error_type] * int(cf.error_type_distribution[error_type]*100)
          type_modification_to_apply = random.choice(list_type_of_error)

        else:
          type_modification_to_apply = type_modification

        # Find an original record that has so far not been used to create - - - - -
        # duplicates
        #
        rand_rec_num = random.randint(0, self.num_org_records)
        org_rec_id = 'rec-%i-org' % (rand_rec_num)

        while (org_rec_id in org_rec_used) or (org_rec_id not in org_rec):
          rand_rec_num = random.randint(0, self.num_org_records) # Get new record number
          org_rec_id = 'rec-%i-org' % (rand_rec_num)

        # Randomly choose how many duplicates to create from this record
        #
        num_dups = utils.random_select(prob_dist_list)

        if (VERBOSE_OUTPUT == True):
          print('  Use record %s to create %i duplicates' % (org_rec_id, num_dups))
          print()

        org_rec_dict = new_org_rec[org_rec_id]  # Get the original record

        d = 0  # Loop counter for duplicates for this record

        # Loop to create duplicate records - - - - - - - - - - - - - - - - - - - -
        #
        while (d < num_dups) and (rec_cnt < self.num_dup_records):

          if (VERBOSE_OUTPUT == True):
            print('  Generate duplicate %d:' % (d+1))

          # Create a duplicate of the original record
          #
          dup_rec_dict = org_rec_dict.copy()  # Make a copy of the original record
          dup_rec_id =   'rec-%i-dup-%i' % (rand_rec_num, d)
          dup_rec_dict['rec_id'] = dup_rec_id

          # Count the number of modifications in this record
          #
          num_modif_in_record = 0

          # Set the field modification counters to zero for all fields
          #
          field_mod_count_dict = {}
          for field_dict in cf.field_list:
            field_mod_count_dict[field_dict['name']] = 0

          # Do random swapping between fields if two or more modifications in
          # record
          #
          if (self.max_num_record_modifi > 1):

            if (type_modification_to_apply == 'typ'):

              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
              # Random swapping of values between a pair of field values
              #
              field_swap_pair_list = list(cf.field_swap_prob.keys())
              random.shuffle(field_swap_pair_list)

              for field_pair in field_swap_pair_list:

                if (random.random() <= cf.field_swap_prob[field_pair]) and \
                  (num_modif_in_record <= (self.max_num_record_modifi-2)):

                  fname_a, fname_b = field_pair

                  # Make sure both fields are in the record dictionary
                  #
                  if (fname_a in dup_rec_dict) and (fname_b in dup_rec_dict):
                    fvalue_a = dup_rec_dict[fname_a]
                    fvalue_b = dup_rec_dict[fname_b]

                    dup_rec_dict[fname_a] = fvalue_b  # Swap field values
                    dup_rec_dict[fname_b] = fvalue_a

                    num_modif_in_record += 2

                    field_mod_count_dict[fname_a] = field_mod_count_dict[fname_a]+1
                    field_mod_count_dict[fname_b] = field_mod_count_dict[fname_b]+1

                    if (VERBOSE_OUTPUT == True):
                      print('    Swapped fields "%s" and "%s": "%s" <-> "%s"' % \
                          (fname_a, fname_b, fvalue_a, fvalue_b))

          # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
          # Now introduce modifications up to the given maximal number
          #
          while (num_modif_in_record < self.max_num_record_modifi):

            # Randomly choose a field
            #
            field_dict = utils.random_select(select_prob_list)
            field_name = field_dict['name']

            # Make sure this field hasn't been modified already
            #
            while (field_mod_count_dict[field_name] == self.max_num_field_modifi):
              field_dict = utils.random_select(select_prob_list)
              field_name = field_dict['name']

            if (field_dict['char_range'] == 'digit'):
              field_range = string.digits
            elif (field_dict['char_range'] == 'alpha'):
              field_range = string.ascii_lowercase
            elif (field_dict['char_range'] == 'alphanum'):
              field_range = string.digits+string.ascii_lowercase

            # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            # Randomly select the number of modifications to be done in this field
            # (and make sure we don't too many modifications in the record)
            #
            num_field_mod_to_do = random.randint(1, self.max_num_field_modifi)

            num_rec_mod_to_do = self.max_num_record_modifi - num_modif_in_record

            if (num_field_mod_to_do > num_rec_mod_to_do):
              num_field_mod_to_do = num_rec_mod_to_do

            num_modif_in_field = 0  # Count  number of modifications in this field

            org_field_val = org_rec_dict.get(field_name, None) # Get original value

            # Loop over chosen number of modifications - - - - - - - - - - - - - -
            #
            for m in range(num_field_mod_to_do):

              old_field_val = dup_rec_dict.get(field_name, None)
              dup_field_val = old_field_val  # Modify this value

              # -------------------------------------------------------------------
              # Typographical modifications
              #
              if (type_modification_to_apply == 'typ'):

                # Randomly choose a modification
                #
                mod_op = utils.random_select(field_dict['prob_list'])

                # Do the selected modification
                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

                # Randomly choose a misspelling if the field value is found in the
                # misspellings dictionary
                #
                if ((mod_op == 'misspell_prob') and \
                    ('misspell_dict' in field_dict) and \
                    (old_field_val in field_dict['misspell_dict'])):

                  misspell_list = field_dict['misspell_dict'][old_field_val]

                  if (len(misspell_list) == 1):
                    dup_field_val = misspell_list[0]
                  else:  # Randomly choose a value
                    dup_field_val = random.choice(misspell_list)

                  if (VERBOSE_OUTPUT == True):
                    print('    Exchanged value "%s" in field "%s" with "%s"' % \
                          (old_field_val, field_name, dup_field_val) + \
                          ' from misspellings dictionary')

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Randomly exchange of a field value with another value
                #
                elif (mod_op == 'val_swap_prob') and (old_field_val != None):

                  if (field_dict['type'] == 'freq'):  # Frequency file based field
                    rand_num = random.randint(0, freq_files_length[field_name]-1)
                    dup_field_val = freq_files[field_name][rand_num]

                  elif (field_dict['type'] == 'date'):  # A date field
                    rand_num = random.randint(field_dict['start_epoch'], \
                                              field_dict['end_epoch']-1)
                    rand_date = utils.epoch_to_date(rand_num)
                    dup_field_val = rand_date[2]+rand_date[1]+rand_date[0]

                  elif (field_dict['type'] == 'phone'):  # A phone number field
                    area_code = random.choice(field_dict['area_codes'])
                    max_digit = int('9'*field_dict['num_digits'])
                    min_digit = int('1' * \
                                    (int(1+round(field_dict['num_digits']/2.))))
                    rand_num = random.randint(min_digit, max_digit)
                    dup_field_val = area_code+' '+ \
                                    str(rand_num).zfill(field_dict['num_digits'])

                  elif (field_dict['type'] == 'ident'):  # Identification no. field
                    rand_num = random.randint(field_dict['start_id'], \
                                              field_dict['end_id']-1)
                    dup_field_val = str(rand_num)

                  if (dup_field_val != old_field_val):
                    if (VERBOSE_OUTPUT == True):
                      print('    Exchanged value in field "%s": "%s" -> "%s"' % \
                            (field_name, old_field_val, dup_field_val))

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Randomly set to missing value
                #
                elif (mod_op == 'miss_prob') and (old_field_val != None):

                  dup_field_val = cf.missing_value  # Set to a missing value

                  if (VERBOSE_OUTPUT == True):
                    print('    Set field "%s" to missing value: "%s" -> "%s"' % \
                            (field_name, old_field_val, dup_field_val))

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Randomly swap two words if the value contains at least two words
                #
                elif ((mod_op == 'wrd_swap_prob') and (old_field_val != None) and \
                      (' ' in old_field_val)):

                  # Count number of words
                  #
                  word_list = old_field_val.split(' ')
                  num_words = len(word_list)

                  if (num_words == 2):  # If only 2 words given
                    swap_index = 0
                  else:  # If more words given select position randomly
                    swap_index = random.randint(0, num_words-2)

                  tmp_word =                word_list[swap_index]
                  word_list[swap_index] =   word_list[swap_index+1]
                  word_list[swap_index+1] = tmp_word

                  dup_field_val = ' '.join(word_list)

                  if (dup_field_val != old_field_val):
                    if (VERBOSE_OUTPUT == True):
                      print('    Swapped words in field "%s": "%s" -> "%s"' % \
                          (field_name, old_field_val, dup_field_val))

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Randomly create a new value if the field value is empty (missing)
                #
                elif (mod_op == 'new_val_prob') and (old_field_val != None):

                  if (field_dict['type'] == 'freq'):  # Frequency file based field
                    rand_num = random.randint(0, freq_files_length[field_name]-1)
                    dup_field_val = freq_files[field_name][rand_num]

                  elif (field_dict['type'] == 'date'):  # A date field
                    rand_num = random.randint(field_dict['start_epoch'], \
                                              field_dict['end_epoch']-1)
                    rand_date = utils.epoch_to_date(rand_num)
                    dup_field_val = rand_date[2]+rand_date[1]+rand_date[0]

                  elif (field_dict['type'] == 'phone'):  # A phone number field
                    area_code = random.choice(field_dict['area_codes'])
                    max_digit = int('9'*field_dict['num_digits'])
                    min_digit = int('1' * \
                                    (int(1+round(field_dict['num_digits']/2.))))
                    rand_num = random.randint(min_digit, max_digit)
                    dup_field_val = area_code+' '+ \
                                  str(rand_num).zfill(field_dict['num_digits'])

                  elif (field_dict['type'] == 'ident'):  # A identification number
                    rand_num = random.randint(field_dict['start_id'], \
                                            field_dict['end_id']-1)
                    dup_field_val = str(rand_num)

                  if (VERBOSE_OUTPUT == True):
                    print('    Exchanged missing value ' + \
                          '"%s" in field "%s" with "%s"' % \
                          (cf.missing_value, field_name, dup_field_val))

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Random substitution of a character
                #
                elif (mod_op == 'sub_prob') and (old_field_val != None):

                  # Get an substitution position randomly
                  #
                  rand_sub_pos = utils.error_position(dup_field_val, 0)

                  if (rand_sub_pos != None):  # If a valid position was returned

                    old_char = dup_field_val[rand_sub_pos]
                    new_char = utils.error_character(old_char, field_dict['char_range'])

                    new_field_val = dup_field_val[:rand_sub_pos] + new_char + \
                                  dup_field_val[rand_sub_pos+1:]

                    if (new_field_val != dup_field_val):
                      dup_field_val = new_field_val

                      if (VERBOSE_OUTPUT == True):
                        print('    Substituted character ' + \
                              '"%s" with "%s" in field ' % \
                              (old_char, new_char) + '"%s": "%s" -> "%s"' % \
                              (field_name, old_field_val, dup_field_val))

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Random insertion of a character
                #
                elif (mod_op == 'ins_prob') and (old_field_val != None):

                  # Get an insert position randomly
                  #
                  rand_ins_pos = utils.error_position(dup_field_val, +1)
                  rand_char =    random.choice(field_range)

                  if (rand_ins_pos != None):  # If a valid position was returned
                    dup_field_val = dup_field_val[:rand_ins_pos] + rand_char + \
                                  dup_field_val[rand_ins_pos:]

                    if (VERBOSE_OUTPUT == True):
                      print('    Inserted char ' + \
                            '"%s" into field "%s": "%s" -> "%s"' % \
                            (rand_char, field_name, old_field_val, dup_field_val))

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Random deletion of a character
                #
                elif ((mod_op == 'del_prob') and (old_field_val != None) and \
                      (len(old_field_val) > 1)):  # Must have at least 2 chars

                  # Get a delete position randomly
                  #
                  rand_del_pos = utils.error_position(dup_field_val, 0)

                  del_char = dup_field_val[rand_del_pos]

                  dup_field_val = dup_field_val[:rand_del_pos] + \
                                  dup_field_val[rand_del_pos+1:]

                  if (VERBOSE_OUTPUT == True):
                    print('    Deleted character ' + \
                          '"%s" in field "%s": "%s" -> "%s"' % \
                          (del_char, field_name, old_field_val, dup_field_val))

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Random transposition of two characters
                #
                elif ((mod_op == 'trans_prob') and (old_field_val != None) and \
                      (len(dup_field_val) > 1)):  # Must have at least 2 chars

                  # Get a transposition position randomly
                  #
                  rand_trans_pos = utils.error_position(dup_field_val, -1)

                  trans_chars = dup_field_val[rand_trans_pos:rand_trans_pos+2]
                  trans_chars2 = trans_chars[1] + trans_chars[0]  # Do transpos.

                  new_field_val = dup_field_val[:rand_trans_pos] + trans_chars2 + \
                                dup_field_val[rand_trans_pos+2:]

                  if (new_field_val != dup_field_val):
                    dup_field_val = new_field_val

                    if (VERBOSE_OUTPUT == True):
                      print('    Transposed characters "%s" in field "%s": "%s"'\
                            % (trans_chars, field_name, old_field_val) + \
                            '-> "%s"' % (dup_field_val))

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Random insertion of a space (thus splitting a word)
                #
                elif ((mod_op == 'spc_ins_prob') and (old_field_val != None) and \
                      (len(dup_field_val.strip()) > 1)):

                  # Randomly select the place where to insert a space (make sure no
                  # spaces are next to this place)
                  #
                  dup_field_val=dup_field_val.strip()

                  rand_ins_pos = utils.error_position(dup_field_val, 0)
                  while (dup_field_val[rand_ins_pos-1] == ' ') or \
                      (dup_field_val[rand_ins_pos] == ' '):
                    rand_ins_pos = utils.error_position(dup_field_val, 0)

                  new_field_val = dup_field_val[:rand_ins_pos] + ' ' + \
                                dup_field_val[rand_ins_pos:]

                  if (new_field_val != dup_field_val):
                    dup_field_val = new_field_val

                    if (VERBOSE_OUTPUT == True):
                      print('    Inserted space " " into field ' + \
                            '"%s": "%s" -> "%s"' % \
                            (field_name, old_field_val, dup_field_val))

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Random deletion of a space (thus merging two words)
                #
                elif ((mod_op == 'spc_del_prob') and (old_field_val != None) and \
                      (' ' in dup_field_val)):  # Field must contain a space char.

                  # Count number of spaces and randomly select one to be deleted
                  #
                  num_spaces = dup_field_val.count(' ')

                  if (num_spaces == 1):
                    space_ind = dup_field_val.index(' ')  # Get index of the space
                  else:
                    rand_space = random.randint(1, num_spaces-1)
                    space_ind = dup_field_val.index(' ', 0)  # Index of first space
                    for i in range(rand_space):
                      # Get index of following spaces
                      space_ind = dup_field_val.index(' ', space_ind)

                  new_field_val = dup_field_val[:space_ind] + \
                                  dup_field_val[space_ind+1:]

                  if (new_field_val != dup_field_val):
                    dup_field_val = new_field_val

                    if (VERBOSE_OUTPUT == True):
                      print('    Deleted space " " from field ' + \
                            '"%s": "%s" -> "%s"' % \
                            (field_name, old_field_val, dup_field_val))

              # -------------------------------------------------------------------
              # Phonetic modifications
              #
              elif ((type_modification_to_apply == 'pho') and \
                    ('pho_prob' in field_dict) and (old_field_val != None)):

                if (random.random() <= field_dict['pho_prob']):
                  phonetic_changes = utils.get_transformation(old_field_val,
                                                        type_modification_to_apply)
                  if (',' in phonetic_changes):
                    tmpstr = phonetic_changes.split(',')
                    pc = tmpstr[1][:-1] # Remove the last ';'
                    list_pc = pc.split(';')
                    ch = random.choice(list_pc)
                    if (ch != ''):
                      dup_field_val = utils.apply_change(old_field_val, ch)

                    if (VERBOSE_OUTPUT == True):
                      print('    Phonetic modification ' + \
                            '"%s" in field "%s": "%s" -> "%s"' % \
                            (ch, field_name, old_field_val, dup_field_val))

              # -------------------------------------------------------------------
              # OCR modifications
              #
              elif ((type_modification_to_apply == 'ocr') and ('ocr_prob' in field_dict) and (old_field_val != None)):

                if (random.random() <= field_dict['ocr_prob']):
                  ocr_changes = utils.get_transformation(old_field_val,
                                                  type_modification_to_apply)
                  if (',' in ocr_changes):
                    tmpstr = ocr_changes.split(',')
                    pc = tmpstr[1][:-1]  # Remove the last ';'
                    list_pc = pc.split(';')
                    ch=random.choice(list_pc)
                    if (ch != ''):
                      dup_field_val = utils.apply_change(old_field_val, ch)

                    if (VERBOSE_OUTPUT == True):
                      print('    OCR modification  "%s" from field "%s": "%s" -> "%s"' %  (ch, field_name, old_field_val, dup_field_val))

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Random deletion of a character (field must contain at least two
                # characters)
                #
                elif ((random.random() <= field_dict['ocr_fail_prob']) and \
                      (len(old_field_val) > 1)):

                  # Get a delete position randomly
                  #
                  rand_del_pos = utils.error_position(dup_field_val, 0)

                  del_char = dup_field_val[rand_del_pos]

                  dup_field_val = dup_field_val[:rand_del_pos] + ' ' + \
                                dup_field_val[rand_del_pos+1:]

                  if (VERBOSE_OUTPUT == True):
                    print('    OCR Failure character ' + \
                          '"%s" in field "%s": "%s" -> "%s"' % \
                          (del_char, field_name, old_field_val, dup_field_val))

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Random insertion of a space (thus splitting a word) (field must
                # contain at least two characters)
                #
                elif ((random.random() <= field_dict['ocr_ins_sp_prob']) and \
                      (len(dup_field_val.strip()) > 1)):

                  # Randomly select the place where to insert a space (make sure
                  # no spaces are next to this place)
                  #
                  dup_field_val = dup_field_val.strip()
                  rand_ins_pos =  utils.error_position(dup_field_val, 0)
                  while ((dup_field_val[rand_ins_pos-1] == ' ') or \
                          (dup_field_val[rand_ins_pos] == ' ')):
                    rand_ins_pos = utils.error_position(dup_field_val, 0)

                  new_field_val = dup_field_val[:rand_ins_pos] + ' ' + \
                                  dup_field_val[rand_ins_pos:]

                  if (new_field_val != dup_field_val):
                    dup_field_val = new_field_val

                    if (VERBOSE_OUTPUT == True):
                      print('    OCR Inserted space " " into field ' + \
                            '"%s": "%s" -> "%s"' % \
                            (field_name, old_field_val, dup_field_val))

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Random deletion of a space (thus merging two words) (field must
                # contain a space character)
                #
                elif ((random.random() <= field_dict['ocr_del_sp_prob']) and \
                      (' ' in dup_field_val)):

                  # Count number of spaces and randomly select one to be deleted
                  #
                  num_spaces = dup_field_val.count(' ')

                  if (num_spaces == 1):
                    space_ind = dup_field_val.index(' ')  # Get index of the space
                  else:
                    rand_space = random.randint(1, num_spaces-1)
                    space_ind = dup_field_val.index(' ', 0)  # Index of first space
                    for i in range(rand_space):
                      # Get index of following spaces
                      space_ind = dup_field_val.index(' ', space_ind)

                  new_field_val = dup_field_val[:space_ind] + \
                                  dup_field_val[space_ind+1:]

                  if (new_field_val != dup_field_val):
                    dup_field_val = new_field_val

                    if (VERBOSE_OUTPUT == True):
                      print('    OCR Deleted space " " from field ' +\
                            '"%s": "%s" -> "%s"' % \
                            (field_name, old_field_val, dup_field_val))

              # Now check if the modified field value is different - - - - - - - -
              #
              if ((old_field_val == org_field_val) and \
                  (dup_field_val != old_field_val)): # The first field modification
                field_mod_count_dict[field_name] = 1
                num_modif_in_record += 1

              elif ((old_field_val != org_field_val) and \
                    (dup_field_val != old_field_val)):  # Following field mods.
                field_mod_count_dict[field_name] += 1
                num_modif_in_record += 1

              if (dup_field_val != old_field_val):
                dup_rec_dict[field_name] = dup_field_val

          # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
          # Now check if the duplicate record differs from the original
          #
          rec_data = dup_rec_dict.copy()  # Make a copy of the record dictionary
          del(rec_data['rec_id'])         # Remove the record identifier
          rec_list = list(rec_data.items())
          rec_list.sort()
          rec_str = str(rec_list)

          if (rec_str not in all_rec_set):  # Check if same record has not already
                                            # been created
            all_rec_set.add(rec_str)
            org_rec_used[org_rec_id] = 1

            dup_rec[dup_rec_id] = dup_rec_dict  # Insert into duplicate records

            d += 1  # Duplicate counter (loop counter)

            rec_cnt += 1

            # Print original and duplicate records field by field - - - - - - - - -
            #
            if (VERBOSE_OUTPUT == True):
              print('  Original and duplicate records:')
              print('    Number of modifications in record: %d' % \
                    (num_modif_in_record))
              print('    Record ID         : %-30s | %-30s' % \
                  (org_rec_dict['rec_id'], dup_rec_dict['rec_id']))
              for field_name in self.field_names:
                print('    %-18s: %-30s | %-30s' % \
                      (field_name, org_rec_dict.get(field_name, cf.missing_value), \
                      dup_rec_dict.get(field_name, cf.missing_value)))
              print()

          else:
            if (VERBOSE_OUTPUT == True):
              print('  No random modifications for record "%s" -> Choose another' \
                    % (dup_rec_id))

          if (VERBOSE_OUTPUT == True):
            print()

    return dup_rec ,org_rec_used
  
  def write_csv_output(self,new_org_rec,dup_rec):
    """ Write output file """
    
    all_rec = new_org_rec  # Merge original and duplicate records

    if (self.num_dup_records > 0):
      all_rec.update(dup_rec)

    all_rec_ids = list(all_rec.keys())  # Get all record IDs and shuffle them randomly
    random.shuffle(all_rec_ids)

    # Make a list of field names and sort them according to column number
    #
    if (self.num_of_hofam_duplicate > 0):
      field_name_list = ['rec_id']+['rec2_id']+self.field_names
    else:
      field_name_list = ['rec_id']+self.field_names

    # Open output file
    #
    try:
      f_out = open(self.output_file, 'w',encoding="utf8")
    except:
      print('Error: Can not write to output file "%s"' % (self.output_file))
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

  def run(self) :
    
    # Initialise random number generator  - - - - - - - - - - - - - - - - - - - - -
    #
    random.seed()         
    start_time = time.time()
    
    # VALIDATE CONFIGURATION
    select_prob_sum  = self._validate_and_sum_prob()
    
    # Create list of select probabilities - - - - - - - - - - - - - - - - - - - - -
    #
    select_prob_list = []
    prob_sum =  0.0

    for field_dict in cf.field_list:
      select_prob_list.append((field_dict, prob_sum))
      prob_sum += field_dict['select_prob']

    # CREATE DISTRIBUTION 
         
    prob_dist_list =  self._duplicate_distribution()
    
    # LOAD FREQUENCY AND LOOKUP TABLES
    print('Step 1: Load and process frequency tables and misspellings dictionaries')       
    freq_files, freq_files_length = self._load_frequency_lookup_tables()  

    # CREATE ORIGINAL RECORDS
    print('Step 2: Create original records')

    all_rec_set = set()  # Set of all records (without identifier) used for
                              # checking that all records are different 
   
    org_rec = self._create_original_records(freq_files_length,freq_files,all_rec_set)

    # CREATE HOUSEHOLD AND FAMILY RECORDS
    print('Step 3: Create household and family records')
  
    new_org_rec = self._create_households_familiy_records(freq_files,freq_files_length,org_rec)
    # CREATE DUPLICATE RECORDS

    print('Step 4: Create duplicate records')
    dup_rec, org_rec_used = self._create_duplicate_records(org_rec,
                                                           prob_dist_list,
                                                           new_org_rec,
                                                           select_prob_list,
                                                           all_rec_set,
                                                           freq_files_length,
                                                           freq_files)
    

    # WRITE OUTPUT CSV FILE

    print('Step 3: Write output file')
    self.write_csv_output(new_org_rec,dup_rec)

def main():
  
 
  # =============================================================================
  # Start main program

  if (len(sys.argv) != 10):
    print('Nine arguments needed with %s:' % (sys.argv[0]))
    print('  - Output file name')
    print('  - Number of original records')
    print('  - Number of duplicate records')
    print('  - Maximal number of duplicate records for one original record')
    print('  - Maximum number of modifications per field')
    print('  - Maximum number of modifications per record')
    print('  - Probability distribution for duplicates (uniform, poisson, zipf)')
    print('  - Type of modification (typo, ocr, phonetic, all)')
    print('  - Number of households and family records')
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
  num_of_hofam_duplicate= int(sys.argv[9])

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

  if (num_of_hofam_duplicate < 0):
    print('Error: Number of Number of households and family records must be  0 or positive')
    sys.exit()

  dsgen = DataSetGen(output_file,
           num_org_records,
           num_dup_records,
           max_num_dups,
           max_num_field_modifi,
           max_num_record_modifi,
           prob_distribution,
           type_modification,
           num_of_hofam_duplicate)
  dsgen.run()

if __name__=="__main__":
  main()