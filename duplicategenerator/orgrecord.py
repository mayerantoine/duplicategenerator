import faker
from faker import Faker
from faker.config import PROVIDERS
import random
from providers.gender import Provider as genderProvider

# List of fields supported  - document the fields supported  - will not support all providers
# a provider can have multiple fields
# We will not need lookup tables OR lookups will move into fake providers
# How to manage dependence 
# State and county providers
# No need for field type# u
# use faker providers or my own ? 
# Can i use faker if i dont have a locale? Can i combine my locales with faker
# national id, medical number provider
# should i put locales as field or not
# how to use frequency and lookup

supported_fields = ['gender','given','surname','age','date_of_birth',
          'ssn','email','address','street_address','city','postcode']

fields = ['gender','given','surname']


class OriginalRecords:
    """  Original records generator"""
    
    def __init__(self,rec_cnt,field_list,locales= None,seed=None):
        self.rec_cnt = rec_cnt
        self.locales = locales
        self.field_list = field_list
        self.seed = seed
        
        if locales is None:    
            self.fake = Faker()
        else:
            self.fake = Faker(locales)
            
        self.fake.seed_instance(seed)
      
    def __iter__(self):        
        for index  in range(self.rec_cnt):
            # add record
            # Check if record was already created
            yield self._create_record()
    
    def _create_record(self):
        
        rec_dict = {}
        for field in self.field_list:
            if field == 'gender':
                self.fake.add_provider(genderProvider)
                rand_val = self.fake.gender()
            elif field == 'given':                        
                if rec_dict['gender'] == 'Female':
                    rand_val = self.fake.first_name_female()
                elif rec_dict['gender'] == 'Male':
                    rand_val = self.fake.first_name_male()
                else :
                    rand_val = 'unknown'
            elif field == 'surname':
                    rand_val = self.fake.last_name()
            elif field == 'date_of_birth' :           
                rand_val = self.fake.date_time()
            elif field == 'ssn':                
                rand_val = self.fake.ssn()
            elif field == 'email':
                rand_val == self.fake.email()
            elif field == 'address':
                rand_val = self.fake.address()
            elif field == 'street_address' :
                rand_val = self.fake.street_address()
            elif field == 'city':
                rand_val = self.fake.city()
            elif field == 'postcode':
                rand_val = self.fake.postcode()
                
            rec_dict[field] = rand_val
            
        return rec_dict       
        

if __name__ == "__main__":
    
    from collections import OrderedDict
    #create_records('fr_FR')
    #print(type(PROVIDERS))
    #print(PROVIDERS)
    #all_providers = [p.split(".")[2] for p in PROVIDERS]
    #print(all_providers)
    
    records = OriginalRecords(5000,fields,'fr_FR')
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


    print(org_rec)
    print(len(all_rec_set))


    
