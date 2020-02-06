import argparse
import logging
import os
import random
import sys
import pandas
import numpy
import json

import unittest
import duplicategenerator


class DuplicateGenTests(unittest.TestCase):
    
        
    def test_validate_no_arguments(self):
        with self.assertRaises(TypeError):
            duplicategenerator.DuplicateGen()
 
    # Test if we can call DuplicateGen with positional arguments 
    def test_validate_positional_arguments(self):
        self.assertIsInstance(duplicategenerator.DuplicateGen(
            num_org_records = 10,
            num_dup_records = 10,
            max_num_dups = 1,
            max_num_field_modifi= 1,
            max_num_record_modifi= 1,
            prob_distribution = "uniform",
            type_modification= "all"
        ),duplicategenerator.generate.DuplicateGen)
            
    
    # Test if we can call DuplicateGen with positional and optional arguments 
    def test_validate_optional_arguments(self):
        self.assertIsInstance(duplicategenerator.DuplicateGen(
            num_org_records = 10,
            num_dup_records = 10,
            max_num_dups = 1,
            max_num_field_modifi= 1,
            max_num_record_modifi= 1,
            prob_distribution = "uniform",
            type_modification= "all",
            verbose_output = False,
            culture = "eng",
            attr_file_name = './duplicategenerator/config/attr_config_file.example.json',
            field_names_prob = {'culture' : 0,'sex': 0.1,'given_name':0.3,'surname':0.3, 'date_of_birth':0.2,'phone_number':0.1}
        ),duplicategenerator.generate.DuplicateGen)
    
    # Test if and error is raised when select_prob sum is > 1
    def test_validate_select_sum_probability(self):
        with self.assertRaises(ValueError):
            duplicategenerator.DuplicateGen(
            num_org_records = 10,
            num_dup_records = 10,
            max_num_dups = 1,
            max_num_field_modifi= 1,
            max_num_record_modifi= 1,
            prob_distribution = "uniform",
            type_modification= "all",
            verbose_output = False,
            culture = "eng",
            attr_file_name = './duplicategenerator/config/attr_config_file.example.json',
            field_names_prob = {'culture' : 0,'sex': 0.1,'given_name':0.5,'surname':0.3, 'date_of_birth':0.2,'phone_number':0.1}
        )
    
     # Test if an error is raised when config file not found
    def test_validate_config_file_exists(self):
        with self.assertRaises(ValueError):
            duplicategenerator.DuplicateGen(
            num_org_records = 10,
            num_dup_records = 10,
            max_num_dups = 1,
            max_num_field_modifi= 1,
            max_num_record_modifi= 1,
            prob_distribution = "uniform",
            type_modification= "all",
            verbose_output = False,
            culture = "eng",
            attr_file_name ='./duplicategenerator/config/attr_config_file.example.json',
            field_names_prob = {'culture' : 0,'sex': 0.1,'given_name':0.5,'surname':0.3, 'date_of_birth':0.2,'phone_number':0.1}
        )
            
            
    # Test if an error is raised when a field is not valid
    def test_validate_field_not_valid(self):
        with self.assertRaises(ValueError):
            duplicategenerator.DuplicateGen(
            num_org_records = 10,
            num_dup_records = 10,
            max_num_dups = 1,
            max_num_field_modifi= 1,
            max_num_record_modifi= 1,
            prob_distribution = "uniform",
            type_modification= "all",
            verbose_output = False,
            culture = "eng",
            attr_file_name = './duplicategenerator/config/attr_config_file.example.json',
            field_names_prob = {'culture' : 0,'sex': 0.1,'name':0.3,'surname':0.3, 'date_of_birth':0.2,'phone_number':0.1}
        )
    
    # Test if generate returns a dicstionaty
    def test_validate_generate(self):
        self.assertIsInstance(duplicategenerator.DuplicateGen(
            num_org_records = 10,
            num_dup_records = 10,
            max_num_dups = 1,
            max_num_field_modifi= 1,
            max_num_record_modifi= 1,
            prob_distribution = "uniform",
            type_modification= "all",
            verbose_output = False,
            culture = "eng",
            attr_file_name = './duplicategenerator/config/attr_config_file.example.json',
            field_names_prob = {'culture' : 0,'sex': 0.1,'given_name':0.3,'surname':0.3, 'date_of_birth':0.2,'phone_number':0.1}
        ).generate(), dict) 
        
        self.assertIsInstance(duplicategenerator.DuplicateGen(
            num_org_records = 10,
            num_dup_records = 10,
            max_num_dups = 1,
            max_num_field_modifi= 1,
            max_num_record_modifi= 1,
            prob_distribution = "uniform",
            type_modification= "all",
            verbose_output = False,
            culture = "eng",
            attr_file_name = './duplicategenerator/config/attr_config_file.example.json',
            field_names_prob = {'culture' : 0,'sex': 0.1,'given_name':0.3,'surname':0.3, 'date_of_birth':0.2,'phone_number':0.1}
        ).generate("dataframe"), pandas.DataFrame)  
        
        self.assertEqual(len(duplicategenerator.DuplicateGen(
            num_org_records = 10,
            num_dup_records = 10,
            max_num_dups = 1,
            max_num_field_modifi= 1,
            max_num_record_modifi= 1,
            prob_distribution = "uniform",
            type_modification= "all",
            verbose_output = False,
            culture = "eng",
            attr_file_name = './duplicategenerator/config/attr_config_file.example.json',
            field_names_prob = {'culture' : 0,'sex': 0.1,'given_name':0.3,'surname':0.3, 'date_of_birth':0.2,'phone_number':0.1}
        ).generate("dataframe").index), 20)          

if __name__ =="__main__" :
    unittest.main()