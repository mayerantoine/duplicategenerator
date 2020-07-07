import faker
from faker import Faker
from faker.config import PROVIDERS, AVAILABLE_LOCALES 
import random
import json
from providers.gender import GenderProvider
from providers.name import NameProvider


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

########### New providers
# gender
# email for dependency
# 

################### Depdendencies
# given_name depends on gender
# age depends date of birth
# phonenumber depends on locale area codes
# email is depenedent on given name
# street adress and city should be interdependant
# state - US state - localized state
# localized zipcode in state

############# Formatting
# Fix date of birth format
# Fix phonenumber format

supported_fields = ['gender','given','surname','age','date_of_birth','phone_number',
          'ssn','email','address','street_address','postcode','city']

fields = ['gender','given_name','surname','date_of_birth','phone_number','email','ssn','street_address','city','postcode']


class OriginalRecords:
    """  Original records generator"""
    
    def __init__(self,rec_cnt,field_list,faker=None,locale= None,seed=None):
        self.rec_cnt = rec_cnt
        self.locale = locale
        self.field_list = field_list
        
        if faker is None:    
            if locale is None:
                self.fake = Faker()
            else:
                self.fake = Faker(locale)
            
            self.fake.seed_instance(seed)
        else: ## using existing faker
            self.fake = faker
        
        self.fake.add_provider(GenderProvider)     
       
    def __iter__(self):        
        for index  in range(self.rec_cnt):
            # add record
            # Check if record was already created
            yield self._create_record()
    
    def _create_record(self):
        
        rec_dict = {}
        for field in self.field_list:
            if field == 'locale':
                rand_val = self.locale
            elif field == 'gender':
                rand_val = self.fake.gender()
            elif field == 'given_name':                        
                if rec_dict['gender'] == 'Female':
                    rand_val = self.fake.first_name_female()
                elif rec_dict['gender'] == 'Male':
                    rand_val = self.fake.first_name_male()
                else :
                    rand_val = 'unknown'
            elif field == 'surname':
                rand_val = self.fake.last_name()
            elif field == 'date_of_birth':           
                rand_val = self.fake.date_of_birth()
            elif field == 'phone_number':
                rand_val = self.fake.phone_number()
            elif field == 'ssn':                
                rand_val = self.fake.ssn()
            elif field == 'email':
                rand_val = self.fake.email()
            elif field == 'address':
                rand_val = self.fake.address()
            elif field == 'street_address' :
                rand_val = self.fake.street_address()
            elif field == 'city':
                rand_val = self.fake.city()
            elif field == 'postcode':
                rand_val = self.fake.postcode()
            else:  ## field not found
                rand_val = None
                raise ValueError(f"Field not found in orginal records generator: {field}")
                
            rec_dict[field] = rand_val
            
        return rec_dict       
        

if __name__ == "__main__":
    
    from collections import OrderedDict
    from pprint import pprint
    
    fake = Faker('en_GB')
    fake.seed_instance(2121)

    records = OriginalRecords(20,fields,fake)
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
    #print(PROVIDERS)
    #print(AVAILABLE_LOCALES )
    #all_providers = [p.split(".")[2] for p in PROVIDERS]
    #print(all_providers)

    #pprint(org_rec)
    #pprint(org_rec.values())
    import pandas
    df = pandas.DataFrame(org_rec.values()).set_index("rec_id")
    print(df)
    #df.to_csv("../original.csv")
    #print(len(all_rec_set))


    
