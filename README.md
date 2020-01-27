# Duplicate generator

The **Duplicate generator** is a libray to create synthetic personal demographic data  such as given name, surname, date of birth and sex  and introduce duplicates  of those records with errors. Those data can used to test or evaluate record linakge and deduplication algorithm.

This project is fork and an udpated version `Freely Extensible Biomedical Record Linkage (FEBRL) <https://sourceforge.net/projects/febrl/>` dataset generator developed  by Agus Pudjijono and Peter Christen in December 2008. For more detailed description please consult the website the ANU Department of Computer Science: `http://datamining.anu.edu.au/projects/linkage-publications.html` or see the paper : `Accurate Synthetic Generation of Realistic Personal Information <http://users.cecs.anu.edu.au/~christen/publications/pakdd2009-submitted.pdf>`.

In this project we upgraded the initial code to python 3.7 , uses pandas, argparse and numpy, we decoupled the configuration from the code. The project is designed to make it easy and simple to generate a customazible  synthetic duplicate personal data.

