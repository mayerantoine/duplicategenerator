# Duplicate generator

The **Duplicate generator** is a libray to create synthetic personal demographic data  such as given name, surname, date of birth and sex  and introduce duplicates  of those records with errors. Those data can used to test or evaluate record linakge and deduplication algorithm.

This project is fork and an udpated version of the  [Freely Extensible Biomedical Record Linkage (FEBRL)](https://sourceforge.net/projects/febrl/) dataset generator developed  by Agus Pudjijono and Peter Christen in December 2008. For more detailed description please consult the website of the  AUSTRALIAN NATIONAL UNIVERSITY(ANU)  Department of Computer Science:(http://datamining.anu.edu.au/projects/linkage-publications.html) or see the paper : [Accurate Synthetic Generation of Realistic Personal Information](http://users.cecs.anu.edu.au/~christen/publications/pakdd2009-submitted.pdf).

In this version we upgraded the initial code to python 3.6 , uses pandas, argparse and numpy, we decoupled the configuration from the code and re-designed the library api to make it easy and simple to generate a customizable  synthetic duplicate personal dataset.

## Basic Usage

```python
import duplicategenerator

dupgen =  duplicategenerator.DuplicateGen(
            num_org_records = 10,
            num_dup_records = 10,
            max_num_dups = 1,
            max_num_field_modifi= 1,
            max_num_record_modifi= 1,
            prob_distribution = "uniform",
            type_modification= "all",
            verbose_output = False,
            culture = "eng",
            attr_file_name = './attr_config_file.example.json',
            field_names_prob = {'culture' : 0,'sex': 0,'given_name':0.3,'surname':0.3, 'date_of_birth':0.15,'phone_number':0.2,'national_identifier':0.05}
        )


df = dupgen.generate("dataframe")
df

   
```

##  Command line Usage

```
python -m duplicategenerator ./test/test5.csv 4000 1000 5 2 2 uniform all --culture eng --config_file ./duplicategenerator/
config/attr_config_file.example.json

```


**NOTE**: This is a beta product. Most of orgininal authors to model phonetic, OCR and typographical modifications functionalities are in an 'alpha' state and have received limited testing.