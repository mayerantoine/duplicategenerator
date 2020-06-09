
![Python](https://github.com/mayerantoine/duplicategenerator/workflows/Python%20application/badge.svg?event=push)
![Coverage Status](https://coveralls.io/repos/github/mayerantoine/duplicategenerator/badge.svg?branch=master)

# Duplicate generator

The **Duplicate generator** is a libray to create synthetic personal demographic data  such as given name, surname, date of birth and sex  and introduce duplicates of those records with errors. Those data can be used to test or evaluate record linkage and deduplication algorithm.

This project is a fork and an udpated version of the  [Freely Extensible Biomedical Record Linkage (FEBRL)](https://sourceforge.net/projects/febrl/) dataset generator developed  by Agus Pudjijono and Peter Christen in December 2008. For more detailed description please consult the website of the  AUSTRALIAN NATIONAL UNIVERSITY(ANU) [Department of Computer Science](http://datamining.anu.edu.au/projects/linkage-publications.html) or see the paper: [Accurate Synthetic Generation of Realistic Personal Information](http://users.cecs.anu.edu.au/~christen/publications/pakdd2009-submitted.pdf).

In this version we upgraded the initial code to python 3.6 , added pandas, argparse and numpy, decoupled the configuration from the code and re-designed the library api to make it easy and simple to generate a customizable synthetic duplicate personal dataset.

## Basic Usage

```python
import duplicategenerator

dupgen =  duplicategenerator.DuplicateGen(
            num_org_records = 4000,
            num_dup_records = 1000,
            max_num_dups = 1,
            max_num_field_modifi= 1,
            max_num_record_modifi= 1,
            prob_distribution = "uniform",
            type_modification= "all",
            verbose_output = False,
            culture = "eng",
            attr_file_name = './attr_config_file.example.json',
            field_names_prob = {'culture' : 0,
                                'sex': 0,
                                'given_name':0.3,
                                'surname':0.3, 
                                'date_of_birth':0.15,
                                'phone_number':0.2,
                                'national_identifier':0.05}
        )


df = dupgen.generate("dataframe")
df

   
```
This will generate a panda dataframe with 5000 records (4000 originals and 1000 duplicates) . The dataset generated is fully customizable using the parameters :

* `num_org_records`  Number of original records to be created
* `num_dup_records`  Number of duplicate records to be created
* `max_num_dups`     The maximum number of duplicates that can be created for one original record
* `max_num_field_modifi` The maximum number of modifications per field
* `max_num_record_modifi`  The maximum number of modifications per record
* `prob_distribution`  The probability distribution used to create the duplicates 
                       (i.e the number of duplicates for one original)
* `type_modification` Select the modification/error types that will be used when duplicates are created
* `verbose_output` Show logging information
* `culture`  Select country or language for names
* `attr_file_name`  Configuration file with errors probability for each field
* `field_names_prob` List of fields in the dataset with the probability to select for modifications/errors 
                      when creating duplicates

##  Command line Usage

```bash
python -m duplicategenerator ./test/test5.csv 4000 1000 5 2 2 uniform all --culture eng --config_file ./duplicategenerator/
config/attr_config_file.example.json

```
To  use the command line you must provide  :

* `output_file` CSV file name to save the data

## Important links and papers
* [Real-world Data is Dirty: Data Cleansing and The Merge/Purge Problem (1998)](http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.46.6676)
* [Accurate Synthetic Generation of Realistic Personal Information](http://users.cecs.anu.edu.au/~christen/publications/pakdd2009-submitted.pdf).


**NOTE**: This is a beta product. Most of the orginal authors functionalities to model phonetic, OCR and typographical modifications are in an 'alpha' state and have received limited testing.