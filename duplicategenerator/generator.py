import copy
import math
import random
import string
import sys
import time
import os
import pandas
import numpy
import json
import logging
import utils
import config as cf

from faker import Faker
from providers.gender import GenderProvider
from providers.name import NameProvider
from orgrecord import OriginalRecords
from duprecord import DuplicateRecords


class Generator:
    
    def __init__(
        self,
        num_org_records,
        num_dup_records,
        max_num_dups,
        max_num_field_modifi,
        max_num_record_modifi,
        prob_distribution,
        type_modification,
        verbose_output=False,
        locale=None,
        attr_file_name=None,
        field_names_prob=None,
        seed=None):

        if locale is None:    
            self.fake = Faker()
        else:
            self.fake = Faker(locale)    
        self.fake.add_provider(GenderProvider)
        self.fake.seed_instance(seed)
               
        self.num_org_records = num_org_records
        self.num_dup_records = num_dup_records
        self.max_num_dups = max_num_dups
        self.max_num_field_modifi = max_num_field_modifi
        self.max_num_record_modifi = max_num_record_modifi
        self.prob_distribution = prob_distribution
        self.type_modification = type_modification

        self.VERBOSE_OUTPUT = verbose_output

        # if none all culture
        # culture should be ISO format
        # list of counttry supported
        # if culture is not there should provide warning
        self.locale = locale

        # have to check file format json
        self.attr_file_name = attr_file_name

        self.single_typo_prob = self._load_attr_configuration("single_typo_prob")
        self.field_swap_prob = self._load_attr_configuration("field_swap_prob")
        self.error_type_distribution = self._load_attr_configuration(
            "error_type_distribution"
        )

        self.field_names_prob = field_names_prob

        self.field_names = list(self.field_names_prob.keys())

        # set field_list based on field_names
        self.field_list = []
        if self.field_names is None:
            self.field_list = list(self._load_attr_configuration("attributes").values())
        else:
            for field_dict in list(
                self._load_attr_configuration("attributes").values()
            ):
                for field in self.field_names:
                    if field_dict["name"] == field:
                        # overwrite select_prob
                        field_dict["select_prob"] = self.field_names_prob[field]
                        self.field_list.append(field_dict)

        # change default attribute select prob to have all fields
        # culture is mandatory or if not all, order is important

        # A list of all probabilities to check ('select_prob' is checked separately)
        self.prob_names = [
            "ins_prob",
            "del_prob",
            "sub_prob",
            "trans_prob",
            "val_swap_prob",
            "wrd_swap_prob",
            "spc_ins_prob",
            "spc_del_prob",
            "miss_prob",
            "misspell_prob",
            "new_val_prob",
        ]

        # VALIDATE CONFIGURATION
        self.select_prob_sum = self._validate_and_sum_prob()

        # Check number of record to modify and number of fields
        if self.max_num_record_modifi < self.max_num_field_modifi:
            raise ValueError(
                "Maximal number of modifications per record must be equal to or larger than maximal number of modifications per field"
            )
        
        self.prob_dist_list = self._duplicate_distribution()
        # _validate json file format and data

    @property
    def num_org_records(self):
        return self._num_org_records

    @num_org_records.setter
    def num_org_records(self, value):
        if value <= 0:
            raise ValueError("Number of original records must be positive")
        self._num_org_records = value

    @property
    def num_dup_records(self):
        return self._num_dup_records

    @num_dup_records.setter
    def num_dup_records(self, value):
        if value <= 0:
            raise ValueError("Number of duplicate records must be zero or positive")
        self._num_dup_records = value

    @property
    def attr_file_name(self):
        return self._attr_file_name

    @attr_file_name.setter
    def attr_file_name(self, value):
        if value is not None:
            if not os.path.exists(value):
                raise ValueError(
                    "Cannot find configuration attributes file.File do not exist!"
                )
        self._attr_file_name = value

    @property
    def max_num_dups(self):
        return self._max_num_dups

    @max_num_dups.setter
    def max_num_dups(self, value):
        if (value <= 0) or (value > 9):
            raise ValueError(
                "Maximal number of duplicates per record must be positive and less than 10"
            )
        self._max_num_dups = value

    @property
    def max_num_record_modifi(self):
        return self._max_num_record_modifi

    @max_num_record_modifi.setter
    def max_num_record_modifi(self, value):
        if value <= 0:
            raise ValueError(
                "Maximal number of modifications per record must be positive"
            )
        self._max_num_record_modifi = value

    @property
    def max_num_field_modifi(self):
        return self._max_num_field_modifi

    @max_num_field_modifi.setter
    def max_num_field_modifi(self, value):
        if value <= 0:
            raise ValueError(
                "Maximal number of modifications per field must be positive"
            )
        self._max_num_field_modifi = value

    @property
    def prob_distribution(self):
        return self._prob_distribution

    @prob_distribution.setter
    def prob_distribution(self, value):
        if value not in ["uni", "poi", "zip", "uniform", "poisson", "zipf"]:
            raise ValueError(
                "Illegal probability distribution must be one of: uniform, poisson, or zipf"
            )
        self._prob_distribution = value

    @property
    def type_modification(self):
        return self._type_modification

    @type_modification.setter
    def type_modification(self, value):
        if value not in ["typ", "ocr", "pho", "all"]:
            raise ValueError(
                'Illegal type of modification must be one of: "typ", "ocr" or "pho" or "all"'
            )
        self._type_modification = value

    @property
    def field_names_prob(self):
        return self._field_names_prob

    @field_names_prob.setter
    def field_names_prob(self, value):
        names_prob = {}
        for field_dict in list(self._load_attr_configuration("attributes").values()):
            names_prob[field_dict["name"]] = field_dict["select_prob"]

        if value is None:
            self._field_names_prob = names_prob
        else:
            # culture field is mandatory
            names = value.keys()
            for field in names:
                if field not in names_prob.keys():
                    raise ValueError(
                        "Unkwown field value, please consult documentation.Field: {}".format(
                            field
                        )
                    )
            if abs(sum(value.values()) - 1) > 0.001:
                raise ValueError("Field select probabilities do not sum to 1.0")
            self._field_names_prob = value
       
       
    def _load_attr_configuration(self, type="attributes"):
        if self._attr_file_name is None:
            attr_data = cf.DEFAULT_ATTR_CONFIG
            return attr_data[type]
        else:
            ## Exception handling
            with open(self.attr_file_name, "r") as json_file:
                attr_data = json.load(json_file)
            return attr_data[type]

    def _validate_and_sum_prob(self):
        """ Check all user options within generate.py for validity  """

        select_prob_sum = 0.0  # Sum over all select probabilities

        # Check if all defined field dictionaries have the necessary keys
        # check name , type , char range, select_prob and prob
        # returns select_prob_sum, update field_dict and field_names
        i = 0  # Loop counter

        for field_dict in self.field_list:

            #  field name
            if "name" not in field_dict:
                print("Error: No field name given for field dictionary")
                raise Exception
            elif field_dict["name"] == "rec_id":
                raise ValueError(
                    'Illegal field name "rec_id" (used for record identifier)'
                )

            # field type
            if field_dict.get("type", "") not in [
                "freq",
                "date",
                "phone",
                "ident",
                "others",
            ]:
                raise ValueError(
                    'Illegal or no field type given for field "%s": %s'
                    % (field_dict["name"], field_dict.get("type", ""))
                )

            # field char_range
            if field_dict.get("char_range", "") not in ["alpha", "alphanum", "digit"]:
                raise ValueError(
                    "Illegal or no random character range given for "
                    + 'field "%s": %s'
                    % (field_dict["name"], field_dict.get("char_range", ""))
                )

            # field type
            if field_dict["type"] == "freq":
                if "freq_file" not in field_dict:
                    raise ValueError('Field of type "freq" has no file name given')

            elif field_dict["type"] == "date":
                if not ("start_date" in field_dict and "end_date" in field_dict):
                    raise ValueError(
                        'Field of type "date" has no start and/or end date given'
                    )

                else:  # Process start and end date
                    start_date = eval(field_dict["start_date"])
                    end_date = eval(field_dict["end_date"])

                    start_epoch = utils.date_to_epoch(
                        start_date[0], start_date[1], start_date[2]
                    )
                    end_epoch = utils.date_to_epoch(
                        end_date[0], end_date[1], end_date[2]
                    )
                    field_dict["start_epoch"] = start_epoch
                    field_dict["end_epoch"] = end_epoch
                    self.field_list[i] = field_dict

            elif field_dict["type"] == "phone":
                if not ("area_codes" in field_dict and "num_digits" in field_dict):
                    raise ValueError(
                        'Field of type "phone" has no area codes and/or number '
                        + "of digits given"
                    )

                else:  # Process area codes and number of digits
                    if isinstance(field_dict["area_codes"], str):  # Only one area code
                        field_dict["area_codes"] = [
                            field_dict["area_codes"]
                        ]  # Make it a list
                    if not isinstance(field_dict["area_codes"], list):
                        raise ValueError(
                            "Area codes given are not a string or a list: %s"
                            % (str(field_dict["area_codes"]))
                        )

                    if not isinstance(field_dict["num_digits"], int):
                        raise ValueError(
                            "Number of digits given is not an integer: %s (%s)"
                            % (
                                str(field_dict["num_digits"]),
                                type(field_dict["num_digits"]),
                            )
                        )

                    self.field_list[i] = field_dict

            elif field_dict["type"] == "ident":
                if not ("start_id" in field_dict and "end_id" in field_dict):
                    raise ValueError(
                        'Field of type "iden" has no start and/or end '
                        + "identification number given"
                    )

            # Check all the probabilities for this field
            if "select_prob" not in field_dict:
                field_dict["select_prob"] = 0.0
            elif (field_dict["select_prob"] < 0.0) or (field_dict["select_prob"] > 1.0):
                raise ValueError(
                    "Illegal value for select probability in dictionary for "
                    + 'field "%s": %f' % (field_dict["name"], field_dict["select_prob"])
                )
            else:
                select_prob_sum += field_dict["select_prob"]

            field_prob_sum = 0.0

            for prob in self.prob_names:
                if prob not in field_dict:
                    field_dict[prob] = 0.0
                elif (field_dict[prob] < 0.0) or (field_dict[prob] > 1.0):
                    raise ValueError(
                        'Illegal value for "%s" probability in dictionary for ' % (prob)
                        + 'field "%s": %f' % (field_dict["name"], field_dict[prob])
                    )

                else:
                    field_prob_sum += field_dict[prob]

            if (field_prob_sum > 0.0) and (abs(field_prob_sum - 1.0) > 0.001):
                raise ValueError(
                    'Sum of probabilities for field "%s" is not 1.0: %f'
                    % (field_dict["name"], field_prob_sum)
                )

            # Create a list of field probabilities and insert into field dictionary
            #
            prob_list = []
            prob_sum = 0.0

            for prob in self.prob_names:
                prob_list.append((prob, prob_sum))
                prob_sum += field_dict[prob]

            field_dict["prob_list"] = prob_list
            self.field_list[
                i
            ] = field_dict  # Store dictionary back into dictionary list

            i += 1
        # end of  fields dictionnaries validation

        if abs(select_prob_sum - 1.0) > 0.001:
            raise ValueError(
                "Field select probabilities do not sum to 1.0: %f" % (select_prob_sum)
            )

        return select_prob_sum

      
    def _duplicate_distribution(self):
        """ Create a distribution for the number of duplicates for an original record """
        
        num_dup = 1
        prob_sum = 0.0
        prob_dist_list = [(num_dup, prob_sum)]
        if (self.prob_distribution == "uni" ):  # Uniform distribution of duplicates - - - -
            uniform_val = 1.0 / float(self.max_num_dups)
            for i in range(self.max_num_dups - 1):
                num_dup += 1
                prob_dist_list.append((num_dup, uniform_val + prob_dist_list[-1][1]))
        
        elif (self.prob_distribution == "poi"):  # Poisson distribution of duplicates - - -
            def fac(n):  # Factorial of an integer number (recursive calculation)
                if n > 1.0:
                    return n * fac(n - 1.0)
                else:
                    return 1.0
            poisson_num = []  # A list of poisson numbers
            poisson_sum = 0.0  # The sum of all poisson number
            # The mean (lambda) for the poisson numbers
            #
            mean = 1.0 + (float(self.num_dup_records) / float(self.num_org_records))
            for i in range(self.max_num_dups):
                poisson_num.append((math.exp(-mean) * (mean ** i)) / fac(i))
                poisson_sum += poisson_num[-1]
            for i in range(self.max_num_dups):  # Scale so they sum up to 1.0
                poisson_num[i] = poisson_num[i] / poisson_sum
            for i in range(self.max_num_dups - 1):
                num_dup += 1
                prob_dist_list.append((num_dup, poisson_num[i] + prob_dist_list[-1][1]))
      
        
        elif (self.prob_distribution == "zip" ):  # Zipf distribution of duplicates - - - - -
            zipf_theta = 0.5
            denom = 0.0
            for i in range(self.num_org_records):
                denom += 1.0 / (i + 1) ** (1.0 - zipf_theta)
            zipf_c = 1.0 / denom
            zipf_num = []  # A list of Zipf numbers
            zipf_sum = 0.0  # The sum of all Zipf number
            for i in range(self.max_num_dups):
                zipf_num.append(zipf_c / ((i + 1) ** (1.0 - zipf_theta)))
                zipf_sum += zipf_num[-1]
            for i in range(self.max_num_dups):  # Scale so they sum up to 1.0
                zipf_num[i] = zipf_num[i] / zipf_sum
            for i in range(self.max_num_dups - 1):
                num_dup += 1
                prob_dist_list.append((num_dup, zipf_num[i] + prob_dist_list[-1][1]))
        
        print("Create %i original and %i duplicate records"
            % (self.num_org_records, self.num_dup_records)
        )
        print(
            "  Distribution of number of duplicates (maximal %i duplicates per record):"
            % (self.max_num_dups)
        )
        print("  %s" % (prob_dist_list))
        return prob_dist_list


    def create_original_records(self):
        
        records = OriginalRecords(self.num_org_records,
                                  self.field_names,
                                  self.fake)
        all_rec_set = set()
        org_rec = {}
        rec_cnt = 0
        for rec_dict  in iter(records):
            rec_list = list(rec_dict.items())
            rec_list.sort()
            rec_str = str(rec_list)
            if rec_str not in all_rec_set:
                all_rec_set.add(rec_str)
                rec_id = f"rec-{rec_cnt}-org"
                rec_dict['rec_id'] = rec_id
                org_rec[rec_id] = rec_dict
                rec_cnt +=1
            else:
                print('***** Record "%s" already created' % (rec_str))
                break

        #pprint(org_rec)
        #pprint(org_rec.values())
        #import pandas
        #df = pandas.DataFrame(org_rec.values()).set_index("rec_id")
        
        return org_rec
     
     
    def _create_duplicate_records(
        self,
        org_rec,
        prob_dist_list,
        new_org_rec,
        select_prob_list,
        all_rec_set,
        freq_files_length,
        freq_files):
        """  
        Create duplicate records 
        
        """

        dup_rec = {}  # Dictionary for duplicate records

        org_rec_used = {}  # Dictionary with record IDs of original records used to
        # create duplicates

        if self.num_dup_records > 0:

            rec_cnt = 0  # Record counter

            while rec_cnt < self.num_dup_records:

                if (
                    self.type_modification == "all"
                ):  # Randomly select an error type according
                    # distribution given in parameter
                    # 'error_type_distribution'
                    list_type_of_error = []
                    for error_type in self.error_type_distribution:
                        list_type_of_error += [error_type] * int(
                            cf.error_type_distribution[error_type] * 100
                        )
                    type_modification_to_apply = random.choice(list_type_of_error)

                else:
                    type_modification_to_apply = self.type_modification

                # Find an original record that has so far not been used to create - - - - -
                # duplicates
                #
                rand_rec_num = random.randint(0, self.num_org_records)
                org_rec_id = "rec-%i-org" % (rand_rec_num)

                while (org_rec_id in org_rec_used) or (org_rec_id not in org_rec):
                     rand_rec_num = random.randint(
                         0, self.num_org_records
                     )  # Get new record number
                     org_rec_id = "rec-%i-org" % (rand_rec_num)
                     #print("Finding original record :",org_rec_id)

                # Randomly choose how many duplicates to create from this record
                #
                num_dups = utils.random_select(prob_dist_list)

                if self.VERBOSE_OUTPUT == True:
                    print(
                        "  Use record %s to create %i duplicates"
                        % (org_rec_id, num_dups)
                    )
                    print()

                org_rec_dict = new_org_rec[org_rec_id]  # Get the original record

                d = 0  # Loop counter for duplicates for this record

                # Loop to create duplicate records - - - - - - - - - - - - - - - - - - - -
                #
                max_retry_num_dups = 10
                retry_num_dups= 0
                while (d < num_dups) and (rec_cnt < self.num_dup_records) and \
                     (retry_num_dups < max_retry_num_dups):

                    if self.VERBOSE_OUTPUT == True:
                        print("  Generate duplicate %d:" % (d + 1))

                    # Create a duplicate of the original record
                    #
                    dup_rec_dict = (
                        org_rec_dict.copy()
                    )  # Make a copy of the original record
                    dup_rec_id = "rec-%i-dup-%i" % (rand_rec_num, d)
                    dup_rec_dict["rec_id"] = dup_rec_id

                    # Count the number of modifications in this record
                    #
                    num_modif_in_record = 0

                    # Set the field modification counters to zero for all fields
                    #
                    field_mod_count_dict = {}
                    for field_dict in self.field_list:
                        field_mod_count_dict[field_dict["name"]] = 0

                    # Do random swapping between fields if two or more modifications in
                    # record
                    #
                    if self.max_num_record_modifi > 1:

                        if type_modification_to_apply == "typ":

                            # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                            # Random swapping of values between a pair of field values
                            #
                            field_swap_pair_list = list(self.field_swap_prob.keys())
                            random.shuffle(field_swap_pair_list)

                            for field_pair in field_swap_pair_list:

                                if (
                                    random.random() <= self.field_swap_prob[field_pair]
                                ) and (
                                    num_modif_in_record
                                    <= (self.max_num_record_modifi - 2)
                                ):

                                    # convert to tuple
                                    field_pair = eval(field_pair)
                                    fname_a, fname_b = field_pair

                                    # Make sure both fields are in the record dictionary
                                    #
                                    if (fname_a in dup_rec_dict) and (
                                        fname_b in dup_rec_dict
                                    ):
                                        fvalue_a = dup_rec_dict[fname_a]
                                        fvalue_b = dup_rec_dict[fname_b]

                                        dup_rec_dict[
                                            fname_a
                                        ] = fvalue_b  # Swap field values
                                        dup_rec_dict[fname_b] = fvalue_a

                                        num_modif_in_record += 2

                                        field_mod_count_dict[fname_a] = (
                                            field_mod_count_dict[fname_a] + 1
                                        )
                                        field_mod_count_dict[fname_b] = (
                                            field_mod_count_dict[fname_b] + 1
                                        )

                                        if self.VERBOSE_OUTPUT == True:
                                            print(
                                                '    Swapped fields "%s" and "%s": "%s" <-> "%s"'
                                                % (fname_a, fname_b, fvalue_a, fvalue_b)
                                            )

                    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                    # Now introduce modifications up to the given maximal number
                    # START WHILE LOOP
                    max_retry_modif_in_record = 10
                    retry_modif_in_record = 0
                    while (num_modif_in_record < self.max_num_record_modifi) and \
                             (retry_modif_in_record < max_retry_modif_in_record) :

                        # Randomly choose a field
                        #
                        field_dict = utils.random_select(select_prob_list)
                        field_name = field_dict["name"]

                        # Make sure this field hasn't been modified already
                        #
                        while (
                            field_mod_count_dict[field_name]
                            == self.max_num_field_modifi
                        ):
                            field_dict = utils.random_select(select_prob_list)
                            field_name = field_dict["name"]

                        if field_dict["char_range"] == "digit":
                            field_range = string.digits
                        elif field_dict["char_range"] == "alpha":
                            field_range = string.ascii_lowercase
                        elif field_dict["char_range"] == "alphanum":
                            field_range = string.digits + string.ascii_lowercase

                        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                        # Randomly select the number of modifications to be done in this field
                        # (and make sure we don't too many modifications in the record)
                        #
                        num_field_mod_to_do = random.randint(
                            1, self.max_num_field_modifi
                        )

                        num_rec_mod_to_do = (
                            self.max_num_record_modifi - num_modif_in_record
                        )

                        if num_field_mod_to_do > num_rec_mod_to_do:
                            num_field_mod_to_do = num_rec_mod_to_do

                        num_modif_in_field = (
                            0  # Count  number of modifications in this field
                        )

                        org_field_val = org_rec_dict.get(
                            field_name, None
                        )  # Get original value

                        # Loop over chosen number of modifications - - - - - - - - - - - - - -
                        #
                        for m in range(num_field_mod_to_do):
                            old_field_val = dup_rec_dict.get(field_name, None)
                            dup_field_val = old_field_val  # Modify this value

                            # -------------------------------------------------------------------
                            # Typographical modifications
                            #
                            if type_modification_to_apply == "typ":

                                # Randomly choose a modification
                                #
                                mod_op = utils.random_select(field_dict["prob_list"])

                                # Do the selected modification
                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

                                # Randomly choose a misspelling if the field value is found in the
                                # misspellings dictionary
                                #
                                if ((mod_op == "misspell_prob")
                                    and ("misspell_dict" in field_dict)
                                    and (old_field_val in field_dict["misspell_dict"])
                                ):

                                    misspell_list = field_dict["misspell_dict"][
                                        old_field_val
                                    ]

                                    if len(misspell_list) == 1:
                                        dup_field_val = misspell_list[0]
                                    else:  # Randomly choose a value
                                        dup_field_val = random.choice(misspell_list)

                                    if self.VERBOSE_OUTPUT == True:
                                        print(
                                            '    Exchanged value "%s" in field "%s" with "%s"'
                                            % (old_field_val, field_name, dup_field_val)
                                            + " from misspellings dictionary"
                                        )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Randomly exchange of a field value with another value
                                #
                                elif (mod_op == "val_swap_prob") and (
                                    old_field_val != None
                                ):

                                    if (
                                        field_dict["type"] == "freq"
                                    ):  # Frequency file based field
                                        rand_num = random.randint(
                                            0, freq_files_length[field_name] - 1
                                        )
                                        dup_field_val = freq_files[field_name][rand_num]

                                    elif field_dict["type"] == "date":  # A date field
                                        rand_num = random.randint(
                                            field_dict["start_epoch"],
                                            field_dict["end_epoch"] - 1,
                                        )
                                        rand_date = utils.epoch_to_date(rand_num)
                                        dup_field_val = (
                                            rand_date[2] + rand_date[1] + rand_date[0]
                                        )

                                    elif (
                                        field_dict["type"] == "phone"
                                    ):  # A phone number field
                                        area_code = random.choice(
                                            field_dict["area_codes"]
                                        )
                                        max_digit = int("9" * field_dict["num_digits"])
                                        min_digit = int(
                                            "1"
                                            * (
                                                int(
                                                    1
                                                    + round(
                                                        field_dict["num_digits"] / 2.0
                                                    )
                                                )
                                            )
                                        )
                                        rand_num = random.randint(min_digit, max_digit)
                                        dup_field_val = (
                                            area_code
                                            + " "
                                            + str(rand_num).zfill(
                                                field_dict["num_digits"]
                                            )
                                        )

                                    elif (
                                        field_dict["type"] == "ident"
                                    ):  # Identification no. field
                                        rand_num = random.randint(
                                            field_dict["start_id"],
                                            field_dict["end_id"] - 1,
                                        )
                                        dup_field_val = str(rand_num)

                                    if dup_field_val != old_field_val:
                                        if self.VERBOSE_OUTPUT == True:
                                            print(
                                                '    Exchanged value in field "%s": "%s" -> "%s"'
                                                % (
                                                    field_name,
                                                    old_field_val,
                                                    dup_field_val,
                                                )
                                            )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Randomly set to missing value
                                #
                                elif (mod_op == "miss_prob") and (old_field_val != None ):

                                    dup_field_val = (
                                        cf.missing_value
                                    )  # Set to a missing value

                                    if self.VERBOSE_OUTPUT == True:
                                        print(
                                            '    Set field "%s" to missing value: "%s" -> "%s"'
                                            % (field_name, old_field_val, dup_field_val)
                                        )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Randomly swap two words if the value contains at least two words
                                #
                                elif (
                                    (mod_op == "wrd_swap_prob")
                                    and (old_field_val != None)
                                    and (" " in old_field_val)
                                ):

                                    # Count number of words
                                    #
                                    word_list = old_field_val.split(" ")
                                    num_words = len(word_list)

                                    if num_words == 2:  # If only 2 words given
                                        swap_index = 0
                                    else:  # If more words given select position randomly
                                        swap_index = random.randint(0, num_words - 2)

                                    tmp_word = word_list[swap_index]
                                    word_list[swap_index] = word_list[swap_index + 1]
                                    word_list[swap_index + 1] = tmp_word

                                    dup_field_val = " ".join(word_list)

                                    if dup_field_val != old_field_val:
                                        if self.VERBOSE_OUTPUT == True:
                                            print(
                                                '    Swapped words in field "%s": "%s" -> "%s"'
                                                % (
                                                    field_name,
                                                    old_field_val,
                                                    dup_field_val,
                                                )
                                            )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Randomly create a new value if the field value is empty (missing)
                                #
                                elif (mod_op == "new_val_prob") and (
                                    old_field_val != None
                                ):

                                    if (
                                        field_dict["type"] == "freq"
                                    ):  # Frequency file based field
                                        rand_num = random.randint(
                                            0, freq_files_length[field_name] - 1
                                        )
                                        dup_field_val = freq_files[field_name][rand_num]

                                    elif field_dict["type"] == "date":  # A date field
                                        rand_num = random.randint(
                                            field_dict["start_epoch"],
                                            field_dict["end_epoch"] - 1,
                                        )
                                        rand_date = utils.epoch_to_date(rand_num)
                                        dup_field_val = (
                                            rand_date[2] + rand_date[1] + rand_date[0]
                                        )

                                    elif (
                                        field_dict["type"] == "phone"
                                    ):  # A phone number field
                                        area_code = random.choice(
                                            field_dict["area_codes"]
                                        )
                                        max_digit = int("9" * field_dict["num_digits"])
                                        min_digit = int(
                                            "1"
                                            * (
                                                int(
                                                    1
                                                    + round(
                                                        field_dict["num_digits"] / 2.0
                                                    )
                                                )
                                            )
                                        )
                                        rand_num = random.randint(min_digit, max_digit)
                                        dup_field_val = (
                                            area_code
                                            + " "
                                            + str(rand_num).zfill(
                                                field_dict["num_digits"]
                                            )
                                        )

                                    elif (
                                        field_dict["type"] == "ident"
                                    ):  # A identification number
                                        rand_num = random.randint(
                                            field_dict["start_id"],
                                            field_dict["end_id"] - 1,
                                        )
                                        dup_field_val = str(rand_num)

                                    if self.VERBOSE_OUTPUT == True:
                                        print(
                                            "    Exchanged missing value "
                                            + '"%s" in field "%s" with "%s"'
                                            % (
                                                cf.missing_value,
                                                field_name,
                                                dup_field_val,
                                            )
                                        )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Random substitution of a character
                                #
                                elif (mod_op == "sub_prob") and (old_field_val != None):

                                    # Get an substitution position randomly
                                    #
                                    rand_sub_pos = utils.error_position(
                                        dup_field_val, 0
                                    )

                                    if (
                                        rand_sub_pos != None
                                    ):  # If a valid position was returned

                                        old_char = dup_field_val[rand_sub_pos]
                                        new_char = utils.error_character(
                                            old_char, field_dict["char_range"]
                                        )

                                        new_field_val = (
                                            dup_field_val[:rand_sub_pos]
                                            + new_char
                                            + dup_field_val[rand_sub_pos + 1 :]
                                        )

                                        if new_field_val != dup_field_val:
                                            dup_field_val = new_field_val

                                            if self.VERBOSE_OUTPUT == True:
                                                print(
                                                    "    Substituted character "
                                                    + '"%s" with "%s" in field '
                                                    % (old_char, new_char)
                                                    + '"%s": "%s" -> "%s"'
                                                    % (
                                                        field_name,
                                                        old_field_val,
                                                        dup_field_val,
                                                    )
                                                )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Random insertion of a character
                                #
                                elif (mod_op == "ins_prob") and (old_field_val != None):

                                    # Get an insert position randomly
                                    #
                                    rand_ins_pos = utils.error_position(
                                        dup_field_val, +1
                                    )
                                    rand_char = random.choice(field_range)

                                    if (
                                        rand_ins_pos != None
                                    ):  # If a valid position was returned
                                        dup_field_val = (
                                            dup_field_val[:rand_ins_pos]
                                            + rand_char
                                            + dup_field_val[rand_ins_pos:]
                                        )

                                        if self.VERBOSE_OUTPUT == True:
                                            print(
                                                "    Inserted char "
                                                + '"%s" into field "%s": "%s" -> "%s"'
                                                % (
                                                    rand_char,
                                                    field_name,
                                                    old_field_val,
                                                    dup_field_val,
                                                )
                                            )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Random deletion of a character
                                #
                                elif ((mod_op == "del_prob") and (old_field_val != None)
                                    and (len(old_field_val) > 1)):  # Must have at least 2 chars

                                    # Get a delete position randomly
                                    #
                                    rand_del_pos = utils.error_position(
                                        dup_field_val, 0
                                    )

                                    del_char = dup_field_val[rand_del_pos]

                                    dup_field_val = (
                                        dup_field_val[:rand_del_pos]
                                        + dup_field_val[rand_del_pos + 1 :]
                                    )

                                    if self.VERBOSE_OUTPUT == True:
                                        print(
                                            "    Deleted character "
                                            + '"%s" in field "%s": "%s" -> "%s"'
                                            % (
                                                del_char,
                                                field_name,
                                                old_field_val,
                                                dup_field_val,
                                            )
                                        )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Random transposition of two characters
                                #
                                elif ( (mod_op == "trans_prob")
                                    and (old_field_val != None)
                                    and (len(dup_field_val) > 1)
                                ):  # Must have at least 2 chars

                                    # Get a transposition position randomly
                                    #
                                    rand_trans_pos = utils.error_position(
                                        dup_field_val, -1
                                    )

                                    trans_chars = dup_field_val[
                                        rand_trans_pos : rand_trans_pos + 2
                                    ]
                                    trans_chars2 = (
                                        trans_chars[1] + trans_chars[0]
                                    )  # Do transpos.

                                    new_field_val = (
                                        dup_field_val[:rand_trans_pos]
                                        + trans_chars2
                                        + dup_field_val[rand_trans_pos + 2 :]
                                    )

                                    if new_field_val != dup_field_val:
                                        dup_field_val = new_field_val

                                        if self.VERBOSE_OUTPUT == True:
                                            print(
                                                '    Transposed characters "%s" in field "%s": "%s"'
                                                % (
                                                    trans_chars,
                                                    field_name,
                                                    old_field_val,
                                                )
                                                + '-> "%s"' % (dup_field_val)
                                            )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Random insertion of a space (thus splitting a word)
                                #
                                elif (
                                    (mod_op == "spc_ins_prob")
                                    and (old_field_val != None)
                                    and (len(dup_field_val.strip()) > 1)
                                ):

                                    # Randomly select the place where to insert a space (make sure no
                                    # spaces are next to this place)
                                    #
                                    dup_field_val = dup_field_val.strip()

                                    rand_ins_pos = utils.error_position(
                                        dup_field_val, 0
                                    )
                                    while (dup_field_val[rand_ins_pos - 1] == " ") or (
                                        dup_field_val[rand_ins_pos] == " "
                                    ):
                                        rand_ins_pos = utils.error_position(
                                            dup_field_val, 0
                                        )

                                    new_field_val = (
                                        dup_field_val[:rand_ins_pos]
                                        + " "
                                        + dup_field_val[rand_ins_pos:]
                                    )

                                    if new_field_val != dup_field_val:
                                        dup_field_val = new_field_val

                                        if self.VERBOSE_OUTPUT == True:
                                            print(
                                                '    Inserted space " " into field '
                                                + '"%s": "%s" -> "%s"'
                                                % (
                                                    field_name,
                                                    old_field_val,
                                                    dup_field_val,
                                                )
                                            )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Random deletion of a space (thus merging two words)
                                #
                                elif (
                                    (mod_op == "spc_del_prob")
                                    and (old_field_val != None)
                                    and (" " in dup_field_val)
                                ):  # Field must contain a space char.

                                    # Count number of spaces and randomly select one to be deleted
                                    #
                                    num_spaces = dup_field_val.count(" ")

                                    if num_spaces == 1:
                                        space_ind = dup_field_val.index(
                                            " "
                                        )  # Get index of the space
                                    else:
                                        rand_space = random.randint(1, num_spaces - 1)
                                        space_ind = dup_field_val.index(
                                            " ", 0
                                        )  # Index of first space
                                        for i in range(rand_space):
                                            # Get index of following spaces
                                            space_ind = dup_field_val.index(
                                                " ", space_ind
                                            )

                                    new_field_val = (
                                        dup_field_val[:space_ind]
                                        + dup_field_val[space_ind + 1 :]
                                    )

                                    if new_field_val != dup_field_val:
                                        dup_field_val = new_field_val

                                        if self.VERBOSE_OUTPUT == True:
                                            print(
                                                '    Deleted space " " from field '
                                                + '"%s": "%s" -> "%s"'
                                                % (
                                                    field_name,
                                                    old_field_val,
                                                    dup_field_val,
                                                )
                                            )

                            # -------------------------------------------------------------------
                            # Phonetic modifications
                            #
                            elif ( (type_modification_to_apply == "pho")
                                and ("pho_prob" in field_dict)
                                and (old_field_val != None)):

                                if random.random() <= field_dict["pho_prob"]:
                                    phonetic_changes = utils.get_transformation(
                                        old_field_val, type_modification_to_apply
                                    )
                                    if "," in phonetic_changes:
                                        tmpstr = phonetic_changes.split(",")
                                        pc = tmpstr[1][:-1]  # Remove the last ';'
                                        list_pc = pc.split(";")
                                        ch = random.choice(list_pc)
                                        if ch != "":
                                            dup_field_val = utils.apply_change(
                                                old_field_val, ch
                                            )
                                        else :     # else  ch = "" ????
                                            retry_modif_in_record +=1
                                   

                                        if self.VERBOSE_OUTPUT == True:
                                            print(
                                                "    Phonetic modification "
                                                + '"%s" in field "%s": "%s" -> "%s"'
                                                % (
                                                    ch,
                                                    field_name,
                                                    old_field_val,
                                                    dup_field_val,
                                                )
                                            )

                            # -------------------------------------------------------------------
                            # OCR modifications
                            #
                            elif ((type_modification_to_apply == "ocr")
                                and ("ocr_prob" in field_dict)
                                and (old_field_val != None)):

                                if random.random() <= field_dict["ocr_prob"]:
                                    ocr_changes = utils.get_transformation(
                                        old_field_val, type_modification_to_apply
                                    )
                                    if "," in ocr_changes:
                                        tmpstr = ocr_changes.split(",")
                                        pc = tmpstr[1][:-1]  # Remove the last ';'
                                        list_pc = pc.split(";")
                                        ch = random.choice(list_pc)
                                        if ch != "":
                                            dup_field_val = utils.apply_change(
                                                old_field_val, ch
                                            )
                                        else:
                                            retry_modif_in_record +=1

                                        if self.VERBOSE_OUTPUT == True:
                                            print(
                                                '    OCR modification  "%s" from field "%s": "%s" -> "%s"'
                                                % (
                                                    ch,
                                                    field_name,
                                                    old_field_val,
                                                    dup_field_val,
                                                )
                                            )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Random deletion of a character (field must contain at least two
                                # characters)
                                #
                                elif (
                                    random.random() <= field_dict["ocr_fail_prob"]
                                ) and (len(old_field_val) > 1):

                                    # Get a delete position randomly
                                    #
                                    rand_del_pos = utils.error_position(dup_field_val, 0)

                                    del_char = dup_field_val[rand_del_pos]

                                    dup_field_val = (
                                        dup_field_val[:rand_del_pos]
                                        + " "
                                        + dup_field_val[rand_del_pos + 1 :]
                                    )

                                    if self.VERBOSE_OUTPUT == True:
                                        print(
                                            "    OCR Failure character "
                                            + '"%s" in field "%s": "%s" -> "%s"'
                                            % (
                                                del_char,
                                                field_name,
                                                old_field_val,
                                                dup_field_val,
                                            )
                                        )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Random insertion of a space (thus splitting a word) (field must
                                # contain at least two characters)
                                #
                                elif (
                                    random.random() <= field_dict["ocr_ins_sp_prob"]
                                ) and (len(dup_field_val.strip()) > 1):

                                    # Randomly select the place where to insert a space (make sure
                                    # no spaces are next to this place)
                                    #
                                    dup_field_val = dup_field_val.strip()
                                    rand_ins_pos = utils.error_position(
                                        dup_field_val, 0
                                    )
                                    while (dup_field_val[rand_ins_pos - 1] == " ") or (
                                        dup_field_val[rand_ins_pos] == " "
                                    ):
                                        rand_ins_pos = utils.error_position(
                                            dup_field_val, 0
                                        )

                                    new_field_val = (
                                        dup_field_val[:rand_ins_pos]
                                        + " "
                                        + dup_field_val[rand_ins_pos:]
                                    )

                                    if new_field_val != dup_field_val:
                                        dup_field_val = new_field_val

                                        if self.VERBOSE_OUTPUT == True:
                                            print(
                                                '    OCR Inserted space " " into field '
                                                + '"%s": "%s" -> "%s"'
                                                % (
                                                    field_name,
                                                    old_field_val,
                                                    dup_field_val,
                                                )
                                            )

                                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                # Random deletion of a space (thus merging two words) (field must
                                # contain a space character)
                                #
                                elif (
                                    random.random() <= field_dict["ocr_del_sp_prob"]
                                ) and (" " in dup_field_val):

                                    # Count number of spaces and randomly select one to be deleted
                                    #
                                    num_spaces = dup_field_val.count(" ")

                                    if num_spaces == 1:
                                        space_ind = dup_field_val.index(
                                            " "
                                        )  # Get index of the space
                                    else:
                                        rand_space = random.randint(1, num_spaces - 1)
                                        space_ind = dup_field_val.index(
                                            " ", 0
                                        )  # Index of first space
                                        for i in range(rand_space):
                                            # Get index of following spaces
                                            space_ind = dup_field_val.index(
                                                " ", space_ind
                                            )

                                    new_field_val = (
                                        dup_field_val[:space_ind]
                                        + dup_field_val[space_ind + 1 :]
                                    )

                                    if new_field_val != dup_field_val:
                                        dup_field_val = new_field_val

                                        if self.VERBOSE_OUTPUT == True:
                                            print(
                                                '    OCR Deleted space " " from field '
                                                + '"%s": "%s" -> "%s"'
                                                % (
                                                    field_name,
                                                    old_field_val,
                                                    dup_field_val,
                                                )
                                            )

                            # Now check if the modified field value is different - - - - - - - -
                            #
                            if (old_field_val == org_field_val) and (
                                dup_field_val != old_field_val
                            ):  # The first field modification
                                field_mod_count_dict[field_name] = 1
                                num_modif_in_record += 1

                            elif (old_field_val != org_field_val) and (
                                dup_field_val != old_field_val
                            ):  # Following field mods.
                                field_mod_count_dict[field_name] += 1
                                num_modif_in_record += 1

                            if dup_field_val != old_field_val:
                                dup_rec_dict[field_name] = dup_field_val
                    
                    # END WHILE LOOP DUPLICATE RECORDS
                    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                    # Now check if the duplicate record differs from the original
                    #
                    rec_data = (
                        dup_rec_dict.copy()
                    )  # Make a copy of the record dictionary
                    del rec_data["rec_id"]  # Remove the record identifier
                    rec_list = list(rec_data.items())
                    rec_list.sort()
                    rec_str = str(rec_list)

                    if (rec_str not in all_rec_set):  # Check if same record has not already
                        # been created
                        all_rec_set.add(rec_str)
                        org_rec_used[org_rec_id] = 1

                        dup_rec[
                            dup_rec_id
                        ] = dup_rec_dict  # Insert into duplicate records

                        d += 1  # Duplicate counter (loop counter)

                        rec_cnt += 1

                        # Print original and duplicate records field by field - - - - - - - - -
                        #
                   
                        if self.VERBOSE_OUTPUT == True:
                            print("  Original and duplicate records:")
                            print(
                                "    Number of modifications in record: %d"
                                % (num_modif_in_record)
                            )
                            print(
                                "    Record ID         : %-30s | %-30s"
                                % (org_rec_dict["rec_id"], dup_rec_dict["rec_id"])
                            )
                            for field_name in self.field_names:
                                print(
                                    "    %-18s: %-30s | %-30s"
                                    % (
                                        field_name,
                                        org_rec_dict.get(field_name, cf.missing_value),
                                        dup_rec_dict.get(field_name, cf.missing_value),
                                    )
                                )
                            print()

                    else:
                        retry_num_dups += 1 
                        if self.VERBOSE_OUTPUT == True:
                            print(
                                '  No random modifications for record "%s" -> Choose another'
                                % (dup_rec_id)
                            )
                                
                    if self.VERBOSE_OUTPUT == True:
                        print()

        return dup_rec, org_rec_used
    
    
    def _create_duplicate(self,org_rec):
        
        if self.num_dup_records > 0:   
        
            dup_rec = {}  # Dictionary for duplicate records
            org_rec_used = {}  # Dictionary with record IDs of original records used to
            rec_cnt = 0
            while rec_cnt < self.num_dup_records  :
            
                # Randomly select an error type according  distribution given in parameter
                # 'error_type_distribution'
                if (self.type_modification == "all" ):      

                    list_type_of_error = []
                    for error_type in self.error_type_distribution:
                        list_type_of_error += [error_type] * int(cf.error_type_distribution[error_type] * 100)

                    type_modification_to_apply = self.fake.random_element(list_type_of_error)
                    
                else:
                    type_modification_to_apply = self.type_modification

            
                # Find an original record that has so far not been used to create duplicates

                rand_rec_num = self.fake.random_int(0, self.num_org_records)
                org_rec_id = "rec-%i-org" % (rand_rec_num)

                while (org_rec_id in org_rec_used) or (org_rec_id not in org_rec):
                    # Get new record number
                    rand_rec_num = self.fake.random_int(0, self.num_org_records) 
                    org_rec_id = "rec-%i-org" % (rand_rec_num)
                    logging.info("Finding original record :",org_rec_id)
                    ## END

                # Randomly choose how many duplicates to create from this record
                #num_dups = utils.random_select(prob_dist_list)
                #num_dups = self.fake.random_element(prob_dist_list)[0]
                #print(num_dups)
                org_rec_dict = org_rec[org_rec_id]  # Get the original record
                duplicates  = DuplicateRecords(
                                field_list = self.field_list,
                                num_org_records = self.num_org_records,
                                num_dup_records = self.num_dup_records,
                                max_num_dups = self.max_num_dups,
                                max_num_field_modifi = self.max_num_field_modifi,
                                max_num_record_modifi = self.max_num_record_modifi,
                                prob_names = self.prob_names,
                                prob_distribution = self.prob_distribution,
                                prob_dist_list = self.prob_dist_list,
                                type_modification = type_modification_to_apply,
                                field_swap_prob = self.field_swap_prob,
                                rand_rec_num = rand_rec_num,
                                org_rec_id = org_rec_id,
                                org_rec = org_rec_dict,
                                faker=self.fake )
                
                ## Loop over duplicates and add them to main dict
                for dup in iter(duplicates):    
                    print(dup)
                rec_cnt +=1
                
                
                
if __name__ == "__main__":
    
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"),
                        format='%(levelname)s: %(asctime)s %(message)s', 
                        datefmt='%m/%d/%Y %I:%M:%S %p')
      
    dupgen = Generator(20,5,3,2,2,"poi","all",False,
                         'fr_FR',
                         './config/attr_config_file.test.json',
                         {'locale' : 0,
                         'gender': 0.05,
                         'given_name':0.3,
                         'surname':0.3, 
                         'date_of_birth':0.1,
                         'phone_number':0.05,
                         'ssn':0.05,
                         'street_address':0.05,
                         'city':0.05,
                         'email':0.05},
                         2121
                         )

#    dupgen = Generator(50,10,5,2,2,"zipf","all",False,
#                         'en_US',
#                         './config/attr_config_file.test.json')
    new_org_rec = {}
    org_rec = dupgen.create_original_records()
    
    from pprint import pprint
    pprint(org_rec)
 
  
    dupgen._create_duplicate(org_rec)
    #print(org_rec)
