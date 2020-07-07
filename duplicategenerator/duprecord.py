import config as cf
from faker import Faker
from providers.duplicate import Provider as DuplicateProvider
from providers.gender import GenderProvider
from providers.name import NameProvider

from duplicategenerator.orgrecord import OriginalRecords

class  DuplicateRecords():
    
    def __init__(self,
                 num_dups,
                 max_num_dups,
                 max_num_field_modifi,
                 max_num_record_modifi,
                 prob_distribution,
                 type_modification,
                 org_rec_id,
                 org_rec,
                 prob_dist_list,
                 select_prob_list,
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
                
        self.num_dups = num_dups
        self.max_num_dups = max_num_dups
        self.max_num_field_modifi = max_num_field_modifi
        self.max_num_record_modifi = max_num_record_modifi
        self.prob_dist_list  = prob_dist_list
        self.type_modification = type_modification
        self.org_rec_id = org_rec_id
        self.org_rec = org_rec
        self.select_prob_list = select_prob_list
    
    def __iter__(self):
        pass
    
    def _create_duplicate(self):
        pass
        
        
        
if __name__ == "__main__":
    
    num_dup_records = 1
    num_org_records = 10
    type_modification = "all"
    error_type_distribution = {"typ": 0.3, "pho": 0.3, "ocr": 0.4}
    
    fake = Faker('en_US')
    fake.seed_instance(2121)
    fake.add_provider(DuplicateProvider)
    
    fields = ['gender','given_name','surname','date_of_birth','phone_number','email','ssn','street_address','city','postcode']

    records = OriginalRecords(num_org_records, fields,fake,'en_US',2121)
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
    
    from pprint import pprint
    pprint(org_rec)
    
    if num_dup_records > 0:   
        
        dup_rec = {}  # Dictionary for duplicate records
        org_rec_used = {}  # Dictionary with record IDs of original records used to
        rec_cnt = 0
        while rec_cnt < num_dup_records :
            
            # Randomly select an error type according  distribution given in parameter
            # 'error_type_distribution'
            if (type_modification == "all" ):      
                
                list_type_of_error = []
                for error_type in error_type_distribution:
                    list_type_of_error += [error_type] * int(cf.error_type_distribution[error_type] * 100)
                            
                type_modification_to_apply = fake.random_element(list_type_of_error)
                print(type_modification_to_apply)
                
            else:
                type_modification_to_apply = type_modification
            
            
            # Find an original record that has so far not been used to create duplicates
                
            rand_rec_num = fake.rand_int(0, num_org_records)
            org_rec_id = "rec-%i-org" % (rand_rec_num)

            while (org_rec_id in org_rec_used) or (org_rec_id not in org_rec):
                # Get new record number
                rand_rec_num = fake.rand_int(0, num_org_records) 
                #org_rec_id = "rec-%i-org" % (rand_rec_num)
                #print("Finding original record :",org_rec_id)
                ## END

                # Randomly choose how many duplicates to create from this record
                #
                #num_dups = utils.random_select(prob_dist_list)
                    
            rec_cnt +=1
            