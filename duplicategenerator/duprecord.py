import math
import logging
import os
import config as cf
from faker import Faker
from providers.duplicate import Provider as DuplicateProvider
from providers.gender import GenderProvider
from providers.name import NameProvider

from orgrecord import OriginalRecords

class  DuplicateRecords():
    
    def __init__(self,
                 field_list,
                 num_org_records,
                 num_dup_records,
                 max_num_dups,
                 max_num_field_modifi,
                 max_num_record_modifi,
                 prob_distribution,
                 prob_dist_list,
                 type_modification,
                 rand_rec_num,
                 org_rec_id,
                 org_rec,
                 prob_names,
                 field_swap_prob,
                 faker=None,
                 locale=None,
                 seed=None):
        
        
        if faker is None:    
            if locale is None:
                self.fake = Faker()
            else:
                self.fake = Faker(locale)
            
            self.fake.seed_instance(seed)
            ## add the duplicate provider
            self.fake.add_provider(DuplicateProvider)
        else: ## using existing faker
            self.fake = faker
        
        self.prob_names = prob_names
        self.field_list = field_list
        self.num_org_records = num_org_records        
        self.num_dup_records = num_dup_records
        self.max_num_dups = max_num_dups
        self.max_num_field_modifi = max_num_field_modifi
        self.max_num_record_modifi = max_num_record_modifi
        # distribution for the number of duplicates for an original record
        self.prob_distribution  = prob_distribution
        self.type_modification = type_modification
        self.rand_rec_num = rand_rec_num,
        self.org_rec_id = org_rec_id
        self.org_rec = org_rec
        self.field_swap_prob = field_swap_prob
        self.prob_dist_list = prob_dist_list 
        self.select_prob_list = []
        prob_sum = 0.0
        for field_dict in self.field_list:
            self.select_prob_list.append((field_dict, prob_sum))
            prob_sum += field_dict["select_prob"]
        
        # Randomly choose how many duplicates to create from this record
        self.num_dups = self.fake.random_element(self.prob_dist_list)[0]
        
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"),
                        format='%(levelname)s: %(asctime)s %(message)s', 
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    
    
    def __repr__(self):
        pass
    
    def _duplicate_distribution(self):
        """ Create a distribution for the number of duplicates for an original record """

        num_dup = 1
        prob_sum = 0.0
        prob_dist_list = [(num_dup, prob_sum)]

        if (
            self.prob_distribution == "uni"
        ):  # Uniform distribution of duplicates - - - -

            uniform_val = 1.0 / float(self.max_num_dups)

            for i in range(self.max_num_dups - 1):
                num_dup += 1
                prob_dist_list.append((num_dup, uniform_val + prob_dist_list[-1][1]))

        elif (
            self.prob_distribution == "poi"
        ):  # Poisson distribution of duplicates - - -

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

        elif (
            self.prob_distribution == "zip"
        ):  # Zipf distribution of duplicates - - - - -
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

        print()
        print(
            "Create %i original and %i duplicate records"
            % (self.num_org_records, self.num_dup_records)
        )
        print(
            "  Distribution of number of duplicates (maximal %i duplicates):"
            % (self.max_num_dups)
        )
        print("  %s" % (prob_dist_list))

        return prob_dist_list
    
    
    def __iter__(self):
        
        d = 0
        max_retry_num_dups = 10
        retry_num_dups= 0
        org_rec_dict = self.org_rec
        
        while ( d < self.num_dups) and (retry_num_dups < max_retry_num_dups):
            logging.info(f"Generate duplicate :{d+1}")
            
            # Create a duplicate of the original record
            dup_rec_dict = (org_rec_dict.copy())  # Make a copy of the original record
            dup_rec_id = "rec-%i-dup-%i" % (rand_rec_num, d)
            dup_rec_dict["rec_id"] = dup_rec_id

            # Count the number of modifications in this record
            num_modif_in_record = 0
  
            # Set the field modification counters to zero for all fields
            field_mod_count_dict = {}
            for field_dict in self.field_list:
                field_mod_count_dict[field_dict["name"]] = 0
            
            # Do random swapping between fields if two or more modifications in record
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

                                logging.info('Swapped fields "%s" and "%s": "%s" <-> "%s"'
                                        % (fname_a, fname_b, fvalue_a, fvalue_b))

            
            max_retry_modif_in_record = 10
            retry_modif_in_record = 0
            
            while (num_modif_in_record < self.max_num_record_modifi) and (retry_modif_in_record < max_retry_modif_in_record) :
        
                # Randomly choose a field
                #field_dict = utils.random_select(select_prob_list)
                field_dict = self.fake.random_select(select_prob_list)
                field_name = field_dict["name"]

                # Make sure this field hasn't been modified already
                while (field_mod_count_dict[field_name] == self.max_num_field_modifi):
                    #field_dict = utils.random_select(select_prob_list)
                    field_dict = self.fake.random_select(select_prob_list)
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
                for m in range(num_field_mod_to_do):
                    old_field_val = dup_rec_dict.get(field_name, None)
                    dup_field_val = old_field_val  # Modify this value
                    
                    dup_field_val = _modify_field(dup_field_val,old_field_val,type_modification)
                    
                    # Now check if the modified field value is d
                    
                if (old_field_val == org_field_val) and (dup_field_val != old_field_val):
                    # The first field modification
                    field_mod_count_dict[field_name] = 1
                    num_modif_in_record += 1
                    
                elif (old_field_val != org_field_val) and (dup_field_val != old_field_val):
                    # Following field mods.
                    field_mod_count_dict[field_name] += 1
                    num_modif_in_record += 1
                    
                if dup_field_val != old_field_val:
                    dup_rec_dict[field_name] = dup_field_val
                
                
            
            
            yield d
            d +=1
        
    
    def _create_duplicates(self):
        # while < num_dups
        # while number of modif per record
        # select a field from record using select_prob_list
        # while number of modif per field
        # based on type of modif
        # select random modif
        # modif field
        
        pass
    
    def _modify_field(self,mod_op,field_type):
        pass
      
if __name__ == "__main__":
    pass
            