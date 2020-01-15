# =============================================================================
#
# For each field (attribute), a dictionary has to be defined with the following
# keys (probabilities can have values between 0.0 and 1.0, or they can be
# missing - in which case it is assumed they have a value of 0.0):
# - name             The field name to be used when a header is written into
#                    the output file.
# - type             The type of the field. Possible are:
#                    'freq'  (for fields that use a frequency table with field
#                             values)
#                    'date'  (for date fields in a certain range)
#                    'phone' (for phone numbers)
#                    'ident' (for numerical identifier fields in a certain
#                             range)
# - char_range       The range of random characters that can be introduced. Can
#                    be one of 'alpha', 'digit', or 'alphanum'.
#
# For fields of type 'freq' the following keys must be given:
# - freq_file        The name of a frequency file.
# - misspell_file    The name of a misspellings file.
#
# For fields of type 'date' the following keys must be given:
# - start_date       A start date, must be a tuple (day,month,year).
# - end_date         A end date, must be a tuple (day,month,year).
#
# For fields of type 'phone' the following keys must be given:
# - area_codes       A list with possible area codes (as strings).
# - num_digits       The number of digits in the phone numbers (without the
#                    area code).
#
# For fields of type 'ident' the following keys must be given:
# - start_id         A start identification number.
# - end_id           An end identification number.
#
# For all fields the following keys must be given:
# - select_prob      Probability of selecting a field for introducing one or
#                    more modifications (set this to 0.0 if no modifications
#                    should be introduced into this field ever). Note: The sum
#                    of these select probabilities over all defined fields must
#                    be 100.
# - depend_prob      If this field is dependent on another field, then this
#                    probability controls how likely the dependency is
#                    followed. If set to 1.0, then the dependency is always
#                    followed.
# - misspell_prob    Probability to swap an original value with a randomly
#                    chosen misspelling from the corresponding misspelling
#                    dictionary (can only be set to larger than 0.0 if such a
#                    misspellings dictionary is defined for the given field).
# - ins_prob         Probability to insert a character into a field value.
# - del_prob         Probability to delete a character from a field value.
# - sub_prob         Probability to substitute a character in a field value
#                    with another character.
# - trans_prob       Probability to transpose two characters in a field value.
# - val_swap_prob    Probability to swap the value in a field with another
#                    (randomly selected) value for this field (taken from this
#                    field's look-up table).
# - wrd_swap_prob    Probability to swap two words in a field (given there are
#                    at least two words in a field).
# - spc_ins_prob     Probability to insert a space into a field value (thus
#                    splitting a word).
# - spc_del_prob     Probability to delete a space (if available) in a field
#                    (and thus merging two words).
# - miss_prob        Probability to set a field value to missing (empty).
# - new_val_prob     Probability to insert a new value given the original value
#                    was empty.
# - pho_prob         Probability to apply a phonetic modification to this field
#                    value.
# - ocr_prob         Probability to apply an OCR modification to this field
#                    value.
# - ocr_fail_prob    Probability that a character is recognised properly, i.e.
#                    that a character is replaced with another, similar
#                    looking, character.
# - ocr_ins_sp_prob  Probability that a space is inserted between two
#                    characters (as an OCR recognition error).
# - ocr_del_sp_prob  Probability that a space is deleted between two words (as
#                    an OCR recognition error). This can of course only happen
#                    is a value contains at least two words.
#
# Optional keys are:
# - depend         A string which contains the name of one or several (comma
#                  separated) other field names upon which this field depends.
#                  For example, a field 'given name could have:
#                    'depend':'culture,sex'
#
# Note: The sum over the probabilities ins_prob, del_prob, sub_prob,
#       trans_prob, val_swap_prob, wrd_swap_prob, spc_ins_prob, spc_del_prob,
#       and miss_prob for each defined field must be 1.0; or 0.0 if no
#       modification should be done at all on a given field.
#
# =============================================================================
# Comments about typographical errors and misspellings found in the literature:
#
# Damerau 1964: - 80% are single errors: insert, delete, substitute or
#                                        transpose
#               - Statistic given: 567/964 (59%) substitutions
#                                  153/964 (16%) deletions
#                                   23/964 ( 2%) transpositions
#                                   99/964 (10%) insertions
#                                  122/964 (13%) multiple errors
#
# Hall 1980: - OCR and other automatic devices introduce similar errors of
#              substitutions, deletions and insertions, but not transpositions;
#              frequency and type of errors are characteristics of the device.
#
# Pollock/Zamora 1984: - OCR output contains almost exclusively substitution
#                        errors which ordinarily account for less than 20% of
#                        key boarded misspellings.
#                      - 90-95% of misspellings in raw keyboarding typically
#                        only contain one error.
#                      - Only 7.8% of the first letter of misspellings were
#                        incorrect, compared to 11.7% of the second and 19.2%
#                        of the third.
#                      - Generally assumed that vowels are less important than
#                        consonants.
#                      - The frequency of a misspelling seems to be determined
#                        more by the frequency of it's parent word than by the
#                        difficulty of spelling it.
#                      - Most errors are mechanical (typos), not the result of
#                        poor spelling.
#                      - The more frequent a letter, the more likely it is to
#                        be miskeyed.
#                      - Deletions are similar frequent than transpositions,
#                        but more frequent than insertions and again more
#                        frequent than substitutions.
#
# Pollock/Zamora 1983: - Study of 50,000 nonword errors, 3-4 character
#                        misspellings constitute only 9.2% of total
#                        misspellings, but they generate 40% of miscorrections.
#
# Peterson 1986: In two studies:
#                - Transpose two letters:  2.6% / 13.1%
#                - Insert letter:         18.7% / 20.3%
#                - Delete letter:         31.6% / 34.4%
#                - Substitute letter:     40.0% / 26.9%
#
# Kukich 1990: - Over 63% of errors in TDD conversations occur in words of
#                length 2, 3 or 4.
#
# Kukich 1992: - 13% of non-word spelling errors in a 40,000 corpus of typed
#                conversations involved merging of two words, 2% splitting a
#                word (often at valid forms, "forgot" -> "for got").
#              - Most misspellings seem to be within two characters in length
#                of the correct spelling.
#
# =============================================================================
# Other comments:
#
# - Intuitively, one can assume that long and unfrequent words are more likely
#   to be misspelt than short and common words.
#
# =============================================================================

import os
import time

givenname_dict = {'name':'given_name',
                  'type':'freq',
            'char_range':'alpha',
           'lookup_file':'data'+os.sep+'givenname-lookup.tbl',
             'freq_file':'data'+os.sep+'givenname-freq.csv',
#             'freq_file':'data-org'+os.sep+'givenname.csv',
#           'select_prob':0.10,
           'select_prob':0.35,
                'depend':'culture,sex',
           'depend_prob':1.00,
         'misspell_file':'data'+os.sep+'givenname-misspell.tbl',
         'misspell_prob':0.30,
              'ins_prob':0.05,
              'del_prob':0.15,
              'sub_prob':0.35,
            'trans_prob':0.05,
         'val_swap_prob':0.02,
         'wrd_swap_prob':0.02,
          'spc_ins_prob':0.01,
          'spc_del_prob':0.01,
             'miss_prob':0.02,
          'new_val_prob':0.02,
              'pho_prob':0.30,
              'ocr_prob':0.01,
         'ocr_fail_prob':0.05,
       'ocr_ins_sp_prob':0.03,
       'ocr_del_sp_prob':0.03}

surname_dict = {'name':'surname',
                'type':'freq',
          'char_range':'alpha',
         'lookup_file':'data'+os.sep+'surname-lookup.tbl',
           'freq_file':'data'+os.sep+'surname-freq.csv',
#           'freq_file':'data-org'+os.sep+'surname.csv',
#         'select_prob':0.09,
         'select_prob':0.30,
              'depend':'culture',
         'depend_prob':1.00,
       'misspell_file':'data'+os.sep+'surname-misspell.tbl',
       'misspell_prob':0.30,
            'ins_prob':0.10,
            'del_prob':0.10,
            'sub_prob':0.35,
          'trans_prob':0.04,
       'val_swap_prob':0.02,
       'wrd_swap_prob':0.02,
        'spc_ins_prob':0.01,
        'spc_del_prob':0.02,
           'miss_prob':0.02,
        'new_val_prob':0.02,
            'pho_prob':0.30,
            'ocr_prob':0.01,
       'ocr_fail_prob':0.05,
     'ocr_ins_sp_prob':0.03,
     'ocr_del_sp_prob':0.03}

title_dict = {'name':'title',
              'type':'freq',
        'char_range':'alpha',
       'lookup_file':'data'+os.sep+'title-sex-age-lookup-freq.tbl',
         'freq_file':'data'+os.sep+'title-freq.csv',
#         'freq_file':'data-org'+os.sep+'title.csv',
       'select_prob':0.01,
            'depend':'sex,age',
       'depend_prob':0.60,
     'misspell_prob':0.30,
           'ins_prob':0.01,
           'del_prob':0.01,
           'sub_prob':0.01,
         'trans_prob':0.01,
      'val_swap_prob':0.01,
      'wrd_swap_prob':0.01,
       'spc_ins_prob':0.01,
       'spc_del_prob':0.02,
          'miss_prob':0.60,
       'new_val_prob':0.01,
           'pho_prob':0.02,
           'ocr_prob':0.01,
      'ocr_fail_prob':0.05,
    'ocr_ins_sp_prob':0.03,
    'ocr_del_sp_prob':0.03}

streetnumber_dict = {'name':'street_number',
                     'type':'freq',
               'char_range':'digit',
                'freq_file':'data'+os.sep+'streetnumber-freq.csv',
#                'freq_file':'data-org'+os.sep+'streetnumber.csv',
              'select_prob':0.10,
                 'ins_prob':0.10,
                 'del_prob':0.15,
                 'sub_prob':0.60,
               'trans_prob':0.05,
            'val_swap_prob':0.05,
            'wrd_swap_prob':0.01,
             'spc_ins_prob':0.00,
             'spc_del_prob':0.00,
                'miss_prob':0.02,
             'new_val_prob':0.02,
                 'pho_prob':0.10,
                 'ocr_prob':0.01,
            'ocr_fail_prob':0.05,
          'ocr_ins_sp_prob':0.03,
          'ocr_del_sp_prob':0.03}

address1_dict = {'name':'address_1',
                 'type':'freq',
           'char_range':'alpha',
            'freq_file':'data'+os.sep+'address1-freq.csv',
#            'freq_file':'data-org'+os.sep+'address1.csv',
          'select_prob':0.10,
             'ins_prob':0.10,
             'del_prob':0.15,
             'sub_prob':0.55,
           'trans_prob':0.05,
        'val_swap_prob':0.02,
        'wrd_swap_prob':0.03,
         'spc_ins_prob':0.02,
         'spc_del_prob':0.03,
            'miss_prob':0.04,
         'new_val_prob':0.01,
             'pho_prob':0.20,
             'ocr_prob':0.01,
        'ocr_fail_prob':0.05,
      'ocr_ins_sp_prob':0.03,
      'ocr_del_sp_prob':0.03}

# Address 2 contains property and institution names - only use rarely
# (set missing probability to a high value)
#
address2_dict = {'name':'address_2',
                 'type':'freq',
           'char_range':'alpha',
            'freq_file':'data'+os.sep+'address2-freq.csv',
#            'freq_file':'data-org'+os.sep+'address2.csv',
          'select_prob':0.10,
             'ins_prob':0.04,
             'del_prob':0.04,
             'sub_prob':0.10,
           'trans_prob':0.02,
        'val_swap_prob':0.03,
        'wrd_swap_prob':0.04,
         'spc_ins_prob':0.02,
         'spc_del_prob':0.01,
            'miss_prob':0.60,
         'new_val_prob':0.10,
             'pho_prob':0.20,
             'ocr_prob':0.01,
        'ocr_fail_prob':0.05,
      'ocr_ins_sp_prob':0.03,
      'ocr_del_sp_prob':0.03}

suburb_dict = {'name':'suburb',
               'type':'freq',
         'char_range':'alpha',
        'lookup_file':'data'+os.sep+'state-suburb-lookup.tbl',
          'freq_file':'data'+os.sep+'suburb-freq.csv',
#          'freq_file':'data-org'+os.sep+'suburb.csv',
        'select_prob':0.10,
             'depend':'state',
        'depend_prob':0.90,
      'misspell_file':'data'+os.sep+'suburb-misspell.tbl',
      'misspell_prob':0.40,
           'ins_prob':0.10,
           'del_prob':0.15,
           'sub_prob':0.22,
         'trans_prob':0.04,
      'val_swap_prob':0.01,
      'wrd_swap_prob':0.02,
       'spc_ins_prob':0.02,
       'spc_del_prob':0.02,
          'miss_prob':0.01,
       'new_val_prob':0.01,
           'pho_prob':0.25,
           'ocr_prob':0.01,
      'ocr_fail_prob':0.05,
    'ocr_ins_sp_prob':0.03,
    'ocr_del_sp_prob':0.03}

postcode_dict = {'name':'postcode',
                 'type':'freq',
           'char_range':'digit',
          'lookup_file':'data'+os.sep+'suburb-postcode-lookup.tbl',
            'freq_file':'data'+os.sep+'postcode-freq.csv',
#            'freq_file':'data-org'+os.sep+'postcode.csv',
          'select_prob':0.05,
               'depend':'state,suburb',
          'depend_prob':0.90,
             'ins_prob':0.00,
             'del_prob':0.00,
             'sub_prob':0.35,
           'trans_prob':0.60,
        'val_swap_prob':0.03,
        'wrd_swap_prob':0.00,
         'spc_ins_prob':0.00,
         'spc_del_prob':0.00,
            'miss_prob':0.01,
         'new_val_prob':0.01,
             'ocr_prob':0.01,
        'ocr_fail_prob':0.05,
      'ocr_ins_sp_prob':0.03,
      'ocr_del_sp_prob':0.03}

state_dict = {'name':'state',
              'type':'freq',
        'char_range':'alpha',
         'freq_file':'data'+os.sep+'state-freq.csv',
#         'freq_file':'data-org'+os.sep+'state.csv',
       'select_prob':0.05,
          'ins_prob':0.10,
          'del_prob':0.10,
          'sub_prob':0.55,
        'trans_prob':0.02,
     'val_swap_prob':0.03,
     'wrd_swap_prob':0.00,
      'spc_ins_prob':0.00,
      'spc_del_prob':0.00,
         'miss_prob':0.10,
      'new_val_prob':0.10,
          'pho_prob':0.10,
          'ocr_prob':0.01,
     'ocr_fail_prob':0.05,
   'ocr_ins_sp_prob':0.03,
   'ocr_del_sp_prob':0.03}

dob_dict = {'name':'date_of_birth',
            'type':'date',
      'char_range':'digit',
      'start_date':(1,1,1900),
        'end_date':(31,12,1999),
#     'select_prob':0.05,
     'select_prob':0.10,
     'depend_prob':1.00,  # Depends on age
        'ins_prob':0.00,
        'del_prob':0.00,
        'sub_prob':0.50,
      'trans_prob':0.30,
   'val_swap_prob':0.05,
   'wrd_swap_prob':0.00,
    'spc_ins_prob':0.00,
    'spc_del_prob':0.00,
       'miss_prob':0.10,
    'new_val_prob':0.05,
        'ocr_prob':0.01,
   'ocr_fail_prob':0.05,
 'ocr_ins_sp_prob':0.03,
 'ocr_del_sp_prob':0.03}

age_dict = {'name':'age',
            'type':'freq',
      'char_range':'digit',
       'freq_file':'data'+os.sep+'age-freq.csv',
     'select_prob':0.05,
     'depend_prob':1.00,  # Depends on date of birth
        'ins_prob':0.00,
        'del_prob':0.00,
        'sub_prob':0.30,
      'trans_prob':0.20,
   'val_swap_prob':0.20,
   'wrd_swap_prob':0.00,
    'spc_ins_prob':0.00,
    'spc_del_prob':0.00,
       'miss_prob':0.20,
    'new_val_prob':0.10,
        'ocr_prob':0.01,
   'ocr_fail_prob':0.05,
 'ocr_ins_sp_prob':0.03,
 'ocr_del_sp_prob':0.03}

sex_dict = {'name':'sex',
            'type':'freq',
      'char_range':'alpha',
       'freq_file':'data'+os.sep+'sex-freq.csv',
#     'select_prob':0.10,
     'select_prob':0.05,
        'ins_prob':0.00,
        'del_prob':0.00,
        'sub_prob':0.30,
      'trans_prob':0.20,
   'val_swap_prob':0.20,
   'wrd_swap_prob':0.00,
    'spc_ins_prob':0.00,
    'spc_del_prob':0.00,
       'miss_prob':0.20,
    'new_val_prob':0.10,
        'pho_prob':0.02,
        'ocr_prob':0.01,
   'ocr_fail_prob':0.05,
 'ocr_ins_sp_prob':0.03,
 'ocr_del_sp_prob':0.03}

culture_dict = {'name':'culture',
                'type':'freq',
          'char_range':'alpha',
           'freq_file':'data'+os.sep+'culture-freq.csv',
         'select_prob':0.00,
            'ins_prob':0.00,
            'del_prob':0.00,
            'sub_prob':0.00,
          'trans_prob':0.00,
       'val_swap_prob':0.00,
       'wrd_swap_prob':0.97,
        'spc_ins_prob':0.00,
        'spc_del_prob':0.00,
           'miss_prob':0.03,
        'new_val_prob':0.00,
            'pho_prob':0.02,
            'ocr_prob':0.01,
       'ocr_fail_prob':0.05,
     'ocr_ins_sp_prob':0.03,
     'ocr_del_sp_prob':0.03}

family_role_dict = {'name':'family_role',
                    'type':'others',
              'char_range':'alpha',
             'select_prob':0.00,
                'ins_prob':0.00,
                'del_prob':0.00,
                'sub_prob':0.00,
              'trans_prob':0.00,
           'val_swap_prob':0.00,
           'wrd_swap_prob':0.00,
            'spc_ins_prob':0.00,
            'spc_del_prob':0.00,
               'miss_prob':0.00,
            'new_val_prob':0.00}

phonenum_dict = {'name':'phone_number',
                 'type':'phone',
           'char_range':'digit',
               #'depend':'state',
          'lookup_file':'data'+os.sep+'state-areacode-lookup.tbl',
           #'area_codes':['02','03','04','07','08'],  # Australian area codes
           #'num_digits':8,                    # For Australian phone numbers
           'num_digits':6,                    # For Ugandan phone numbers
           'area_codes':['772','774','782','752','712'],  # Ugandan area codes
          'select_prob':0.15,
          #'depend_prob':0.90,
             'ins_prob':0.00,
             'del_prob':0.00,
             'sub_prob':0.40,
           'trans_prob':0.30,
        'val_swap_prob':0.15,
        'wrd_swap_prob':0.00,
         'spc_ins_prob':0.00,
         'spc_del_prob':0.00,
            'miss_prob':0.05,
         'new_val_prob':0.10,
             'ocr_prob':0.01,
        'ocr_fail_prob':0.05,
      'ocr_ins_sp_prob':0.03,
      'ocr_del_sp_prob':0.03}

ssid_dict = {'name':'soc_sec_id',
             'type':'ident',
       'char_range':'digit',
         #'start_id':1000000,
           #'end_id':9999999,
           'start_id':10000000, # 8 digits for Uganda NIN
           'end_id':99999999,
      'select_prob':0.05,
         'ins_prob':0.00,
         'del_prob':0.00,
         'sub_prob':0.50,
       'trans_prob':0.40,
    'val_swap_prob':0.10,
    'wrd_swap_prob':0.00,
     'spc_ins_prob':0.00,
     'spc_del_prob':0.00,
        'miss_prob':0.00,
     'new_val_prob':0.00,
         'ocr_prob':0.01,
    'ocr_fail_prob':0.05,
  'ocr_ins_sp_prob':0.03,
  'ocr_del_sp_prob':0.03}

# Create a field which can be used for blocking (generate values 0 to 9 which
# are not modified in duplicates).
#
blocking_dict = {'name':'blocking_number',
                 'type':'ident',
           'char_range':'digit',
             'start_id':0,
               'end_id':10,
          'select_prob':0.00,
             'ins_prob':0.00,
             'del_prob':0.00,
             'sub_prob':0.00,
           'trans_prob':0.00,
        'val_swap_prob':0.00,
        'wrd_swap_prob':0.00,
         'spc_ins_prob':0.00,
         'spc_del_prob':0.00,
            'miss_prob':0.00,
         'new_val_prob':0.00}

# -----------------------------------------------------------------------------
# Probabilities (between 0.0 and 1.0) for swapping values between two fields.
# Use field names as defined in the field directories (keys 'name').
#
field_swap_prob = {('address_1',  'address_2'):0.02,
                   ('given_name', 'surname'):  0.05,
                   ('postcode',   'suburb'):   0.01}

# -----------------------------------------------------------------------------
# Probabilities (between 0.0 and 1.0) for creating a typographical error (a new
# character) in the same row or the same column. This is used in the random
# selection of a new character in the 'sub_prob' (substitution of a character
# in a field).
#
single_typo_prob = {'same_row':0.40,
                    'same_col':0.30}

# -----------------------------------------------------------------------------
# Now add all field dictionaries into a list according to how they should be
# saved in the output file.
#
#field_list = [culture_dict, sex_dict, age_dict, dob_dict, title_dict,
#              givenname_dict, surname_dict, state_dict, suburb_dict,
#              postcode_dict, streetnumber_dict, address1_dict, address2_dict,
#              phonenum_dict, ssid_dict, blocking_dict, family_role_dict]


field_list = [culture_dict, sex_dict, dob_dict,
              givenname_dict, surname_dict, phonenum_dict,ssid_dict,blocking_dict]
# -----------------------------------------------------------------------------
# Flag for writing a header line (keys 'name' of field dictionaries).
#
save_header = True  # Set to 'False' if no header should be written

# -----------------------------------------------------------------------------
# String to be inserted for missing values.
#
missing_value = ''

# String to be inserted for blank values.
#
blank_value = ' '

# -----------------------------------------------------------------------------
# Current year
#
current_year = time.localtime()[0]  # Alternatively set manual

# -----------------------------------------------------------------------------
# Household freq files
#
household_freq_dict = {'age' : 'data'+os.sep+'household-age-freq.csv',
                       'sex' : 'data'+os.sep+'household-sex-freq.csv'}

# -----------------------------------------------------------------------------
# Distribution of the number of household and family records to be generated
#
household_prob = 0.4
family_prob    = 0.6

# -----------------------------------------------------------------------------
# List of fields that are not modified when family or household records are
# generated
#
household_field_list =  ['street_number','address_1','address_2','suburb',
                         'postcode','state','phone_number']
family_field_list    =  ['surname','street_number','address_1','address_2',
                         'suburb','postcode','state','phone_number']

# -----------------------------------------------------------------------------
# Error type distribution
#
error_type_distribution = {'typ' : 0.3,
                           'pho' : 0.3,
                           'ocr' : 0.4}
