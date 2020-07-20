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
                 num_dups,
                 max_num_dups,
                 max_num_field_modifi,
                 max_num_record_modifi,
                 prob_distribution,
                 type_modification,
                 org_rec_id,
                 org_rec,
                 prob_names,
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
        self.num_dups = num_dups
        self.max_num_dups = max_num_dups
        self.max_num_field_modifi = max_num_field_modifi
        self.max_num_record_modifi = max_num_record_modifi
        # distribution for the number of duplicates for an original record
        self.prob_distribution  = prob_distribution
        self.type_modification = type_modification
        self.org_rec_id = org_rec_id
        self.org_rec = org_rec
    
    
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
        pass
    
    def _create_duplicates(self):
        # while < num_dups
        pass
       
if __name__ == "__main__":
    
    org_rec_1 = {'city': 'Lake Edwinberg',
               'date_of_birth': datetime.date(1961, 9, 17),
               'email': 'james41@mcclure.com',
               'gender': 'Female',
               'given_name': 'Melissa',
               'phone_number': '+1-840-804-5074x6177',
               'postcode': '58505',
               'rec_id': 'rec-7-org',
               'ssn': '290-62-4322',
               'street_address': '1227 West Light Suite 536',
               'surname': 'Stanley'}
    
    org_rec_2 = {'city': 'New Maria',
               'date_of_birth': datetime.date(1956, 10, 1),
               'email': 'joshuajimenez@smith.net',
               'gender': 'Female',
               'given_name': 'Selena',
               'phone_number': '070.451.9189x3171',
               'postcode': '56930',
               'rec_id': 'rec-6-org',
               'ssn': '106-91-4015',
               'street_address': '750 Jeffery Ports Suite 736',
               'surname': 'Mullen'}
    
    fake = Faker('en_GB')
    fake.seed_instance(2121)
    
    dup_rec = DuplicateRecords(
        field_list = fields,
        num_org_records = 5000,
        num_dups=5,
        max_num_dups=5,
        max_num_field_modifi=2,
        max_num_record_modifi=2,
        prob_names = names,
        prob_distribution="poi",
        type_modification="typ",
        org_rec_id='rec-1-org',
        org_rec=org_rec_1,
        faker=fake )   

            