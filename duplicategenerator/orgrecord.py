import faker
from faker import Faker
from faker.config import PROVIDERS
import random


# List of fields supported  - document the fields supported  - will not support all providers
# a provider can have multiple fields
supported_fields = ['sex','given','surname','date_of_birth',
          'ssn','email','address','street_address','city','postcode']

fields = ['sex','given','surname','date_of_birth','street_address','city','postcode']


class OriginalRecords:
    """  Original records generator"""
    
    def __init__(self,rec_cnt,locales,field_list,seed=None):
        self.rec_cnt = rec_cnt
        self.locales = locales
        self.field_list = field_list
        self.seed = seed
        self.fake = Faker(locales)
        self.fake.seed_instance(seed)
      
    def __iter__(self):        
        for index  in range(self.rec_cnt):
            yield self._create_record()
    
    def _create_record(self):
        
        rec_dict = {}
        for field in self.field_list:
            if field == 'sex':
                rand_val = random.choices(['F','M'],[1,1],k=1)[0]
            elif field == 'given':                        
                if rec_dict['sex'] == 'F':
                    rand_val = self.fake.first_name_female()
                elif rec_dict['sex'] == 'M':
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
    #create_records('fr_FR')
    #print(type(PROVIDERS))
    #print(PROVIDERS)
    all_providers = [p.split(".")[2] for p in PROVIDERS]
    #print(all_providers)
    records = OriginalRecords(2,'fr_FR',fields)
    org_rec = {}
    rec_cnt = 0
    for item in iter(records):
        rec_id = f"rec-{rec_cnt}-org"
        org_rec[rec_id] = item
        rec_cnt +=1
    
    print(org_rec)
    


    
