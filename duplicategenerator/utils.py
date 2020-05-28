import math
import os
import random
import string
import sys
import time

days_in_month = [
    [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
    [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
]


# -----------------------------------------------------------------------------
# Probabilities (between 0.0 and 1.0) for creating a typographical error (a new
# character) in the same row or the same column. This is used in the random
# selection of a new character in the 'sub_prob' (substitution of a character
# in a field).
#
single_typo_prob = {"same_row": 0.40, "same_col": 0.30}

# ---------------------------------------------------------------
ocr_rules_file = "lib_ocr_rules.txt"
phonetic_rules_file = "lib_phonetic_rules.txt"


# =============================================================================
# Functions used by the main program come here


def error_position(input_string, len_offset):
    """A function that randomly calculates an error position within the given
     input string and returns the position as integer number 0 or larger.

     The argument 'len_offset' can be set to an integer (e.g. -1, 0, or 1) and
     will give an offset relative to the string length of the maximal error
     position that can be returned.

     Errors do not likely appear at the beginning of a word, so a gauss random
     distribution is used with the mean being one position behind half the
     string length (and standard deviation 1.0)
  """

    str_len = len(input_string)
    max_return_pos = str_len - 1 + len_offset  # Maximal position to be returned

    if str_len == 0:
        return None  # Empty input string

    mid_pos = (str_len + len_offset) / 2 + 1

    random_pos = random.gauss(float(mid_pos), 1.0)
    random_pos = max(0, int(round(random_pos)))  # Make it integer and 0 or larger

    return min(random_pos, max_return_pos)


# -----------------------------------------------------------------------------


def error_character(input_char, char_range):
    """A function which returns a character created randomly. It uses row and
     column keyboard dictionaires.
  """

    # Keyboard substitutions gives two dictionaries with the neigbouring keys for
    # all letters both for rows and columns (based on ideas implemented by
    # Mauricio A. Hernandez in his dbgen).
    #
    rows = {
        "a": "s",
        "b": "vn",
        "c": "xv",
        "d": "sf",
        "e": "wr",
        "f": "dg",
        "g": "fh",
        "h": "gj",
        "i": "uo",
        "j": "hk",
        "k": "jl",
        "l": "k",
        "m": "n",
        "n": "bm",
        "o": "ip",
        "p": "o",
        "q": "w",
        "r": "et",
        "s": "ad",
        "t": "ry",
        "u": "yi",
        "v": "cb",
        "w": "qe",
        "x": "zc",
        "y": "tu",
        "z": "x",
        "1": "2",
        "2": "13",
        "3": "24",
        "4": "35",
        "5": "46",
        "6": "57",
        "7": "68",
        "8": "79",
        "9": "80",
        "0": "9",
    }

    cols = {
        "a": "qzw",
        "b": "gh",
        "c": "df",
        "d": "erc",
        "e": "d",
        "f": "rvc",
        "g": "tbv",
        "h": "ybn",
        "i": "k",
        "j": "umn",
        "k": "im",
        "l": "o",
        "m": "jk",
        "n": "hj",
        "o": "l",
        "p": "p",
        "q": "a",
        "r": "f",
        "s": "wxz",
        "t": "gf",
        "u": "j",
        "v": "fg",
        "w": "s",
        "x": "sd",
        "y": "h",
        "z": "as",
    }

    rand_num = random.random()  # Create a random number between 0 and 1

    if char_range == "digit":

        # A randomly chosen neigbouring key in the same keyboard row
        #
        if (input_char.isdigit()) and (rand_num <= single_typo_prob["same_row"]):
            output_char = random.choice(rows[input_char])
        else:
            choice_str = str.replace(string.digits, input_char, "")
            output_char = random.choice(choice_str)  # A randomly choosen digit

    elif char_range == "alpha":

        # A randomly chosen neigbouring key in the same keyboard row
        #
        if (input_char.isalpha()) and (rand_num <= single_typo_prob["same_row"]):
            output_char = random.choice(rows[input_char])

        # A randomly chosen neigbouring key in the same keyboard column
        #
        elif (input_char.isalpha()) and (
            rand_num <= (single_typo_prob["same_row"] + single_typo_prob["same_col"])
        ):
            output_char = random.choice(cols[input_char])
        else:
            choice_str = str.replace(string.ascii_lowercase, input_char, "")
            output_char = random.choice(choice_str)  # A randomly choosen letter

    else:  # Both letters and digits possible

        # A randomly chosen neigbouring key in the same keyboard row
        #
        if rand_num <= single_typo_prob["same_row"]:
            if input_char in rows:
                output_char = random.choice(rows[input_char])
            else:
                choice_str = str.replace(
                    string.ascii_lowercase + string.digits, input_char, ""
                )
                output_char = random.choice(choice_str)  # A randomly choosen character

        # A randomly chosen neigbouring key in the same keyboard column
        #
        elif rand_num <= (single_typo_prob["same_row"] + single_typo_prob["same_col"]):
            if input_char in cols:
                output_char = random.choice(cols[input_char])
            else:
                choice_str = str.replace(
                    string.ascii_lowercase + string.digits, input_char, ""
                )
                output_char = random.choice(choice_str)  # A randomly choosen character

        else:
            choice_str = str.replace(
                string.ascii_lowercase + string.digits, input_char, ""
            )
            output_char = random.choice(choice_str)  # A randomly choosen character

    return output_char


# -----------------------------------------------------------------------------

# Some simple funcions used for date conversions follow
# (based on functions from the 'normalDate.py' module by Jeff Bauer, see:
# http://starship.python.net/crew/jbauer/normalDate/)


def first_day_of_year(year):
    """Calculate the day number (relative to 1 january 1900) of the first day in
     the given year.
  """

    if year == 0:
        print("Error: A year value of 0 is not possible")
        raise Exception

    elif year < 0:
        first_day = (year * 365) + int((year - 1) / 4) - 693596
    else:  # Positive year
        leap_adj = int((year + 3) / 4)
        if year > 1600:
            leap_adj = (
                leap_adj
                - int((year + 99 - 1600) / 100)
                + int((year + 399 - 1600) / 400)
            )

        first_day = year * 365 + leap_adj - 693963

        if year > 1582:
            first_day -= 10

    return first_day


# -----------------------------------------------------------------------------


def is_leap_year(year):
    """Determine if the given year is a leap year. Returns 0 (no) or 1 (yes).
  """

    if year < 1600:
        if (year % 4) != 0:
            return 0
        else:
            return 1

    elif (year % 4) != 0:
        return 0

    elif (year % 100) != 0:
        return 1

    elif (year % 400) != 0:
        return 0

    else:
        return 1


# -----------------------------------------------------------------------------


def epoch_to_date(daynum):
    """Convert an epoch day number into a date [day, month, year], with
     day, month and year being strings of length 2, 2, and 4, respectively.
     (based on a function from the 'normalDate.py' module by Jeff Bauer, see:
     http://starship.python.net/crew/jbauer/normalDate/)

  USAGE:
    [year, month, day] = epoch_to_date(daynum)

  ARGUMENTS:
    daynum  A integer giving the epoch day (0 = 1 January 1900)

  DESCRIPTION:
    Function for converting a number of days (integer value) since epoch time
    1 January 1900 (integer value) into a date tuple [day, month, year].

  EXAMPLES:
    [day, month, year] = epoch_to_date(0)      # returns ['01','01','1900']
    [day, month, year] = epoch_to_date(37734)  # returns ['25','04','2003']
  """

    if not (isinstance(daynum, int) or isinstance(daynum, int)):
        print(
            'Error: Input value for "daynum" is not of integer type: %s' % (str(daynum))
        )
        raise Exception

    if daynum >= -115860:
        year = 1600 + int(math.floor((daynum + 109573) / 365.2425))
    elif daynum >= -693597:
        year = 4 + int(math.floor((daynum + 692502) / 365.2425))
    else:
        year = -4 + int(math.floor((daynum + 695058) / 365.2425))

    days = daynum - first_day_of_year(year) + 1

    if days <= 0:
        year -= 1
        days = daynum - first_day_of_year(year) + 1

    days_in_year = 365 + is_leap_year(year)  # Adjust for a leap year

    if days > days_in_year:
        year += 1
        days = daynum - first_day_of_year(year) + 1

    # Add 10 days for dates between 15 October 1582 and 31 December 1582
    #
    if (daynum >= -115860) and (daynum <= -115783):
        days += 10

    day_count = 0
    month = 12
    leap_year_flag = is_leap_year(year)

    for m in range(12):
        day_count += days_in_month[leap_year_flag][m]
        if day_count >= days:
            month = m + 1
            break

    # Add up the days in the prior months
    #
    prior_month_days = 0
    for m in range(month - 1):
        prior_month_days += days_in_month[leap_year_flag][m]

    day = days - prior_month_days

    day_str = str.zfill(str(day), 2)  # Add '0' if necessary
    month_str = str.zfill(str(month), 2)  # Add '0' if necessary
    year_str = str(year)  # Is always four digits long

    return [day_str, month_str, year_str]


# -----------------------------------------------------------------------------


def date_to_epoch(day, month, year):
    """ Convert a date [day, month, year] into an epoch day number.
     (based on a function from the 'normalDate.py' module by Jeff Bauer, see:
     
     http://starship.python.net/crew/jbauer/normalDate/)

  USAGE:
    daynum = date_to_epoch(year, month, day)

  ARGUMENTS:
    day    Day value (string or integer number)
    month  Month value (string or integer number)
    year   Year value (string or integer number)

  DESCRIPTION:
    Function for converting a date into a epoch day number (integer value)
    since 1 january 1900.

  EXAMPLES:
    day = date_to_epoch('01', '01', '1900')  # returns 0
    day = date_to_epoch('25', '04', '2003')  # returns 37734
  """

    # Convert into integer values
    #
    try:
        day_int = int(day)
    except:
        print('Error: "day" value is not an integer')
        raise Exception
    try:
        month_int = int(month)
    except:
        print('Error: "month" value is not an integer')
        raise Exception
    try:
        year_int = int(year)
    except:
        print('Error: "year" value is not an integer')
        raise Exception

    # Test if values are within range
    #
    if year_int <= 1000:
        print(
            'Error: Input value for "year" is not a positive integer '
            + "number: %i" % (year)
        )
        raise Exception

    leap_year_flag = is_leap_year(year_int)

    if (month_int <= 0) or (month_int > 12):
        print(
            'Error: Input value for "month" is not a possible day number: %i' % (month)
        )
        raise Exception

    if (day_int <= 0) or (day_int > days_in_month[leap_year_flag][month_int - 1]):
        print('Error: Input value for "day" is not a possible day number: %i' % (day))
        raise Exception

    days = first_day_of_year(year_int) + day_int - 1

    for m in range(month_int - 1):
        days += days_in_month[leap_year_flag][m]

    if year_int == 1582:
        if (month_int > 10) or ((month_int == 10) and (day_int > 4)):
            days -= 10

    return days


# -----------------------------------------------------------------------------


def load_misspellings_dict(misspellings_file_name):
    """Load a look-up table containing misspellings for common words, which can
     be used to introduce realistic errors.

     Returns a dictionary where the keys are the correct spellings and the
     values are a list of one or more misspellings.
  """

    # Open file and read all lines into a list
    #
    try:
        f = open(misspellings_file_name, "r", encoding="utf8")
    except:
        print(
            'Error: Can not read from misspellings file "%s"' % (misspellings_file_name)
        )
        raise IOError

    file_data = f.readlines()  # Read complete file
    f.close()

    misspell_dict = {}

    key = None  # Start with a non-existing key word (correct word)

    # Now process all lines - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    for line in file_data:
        l = line.strip()  # Remove line separators

        if (len(l) > 0) and (l[0] != "#"):  # Not empty line and not comment

            ll = l.split(":")  # Separate key from values

            if (ll[0] == "") and (len(ll) > 1):
                ll = ll[1:]

            if len(ll) == 2:  # Line contains a key - - - - - - - - - - - - - - - -

                key = ll[0].strip().lower()  # Get key, make lower and strip spaces

                if key == "":
                    print('This should not happen: "%s"' % (l))
                    raise Exception

                vals = ll[1].strip().lower()  # Get values in a string

                if vals == "":
                    print(
                        'Error: No misspellings given for "%s" in line: "%s"' % (key, l)
                    )
                    raise Exception

                val_list = vals.split(",")
                val_set = set()
                for val in val_list:
                    if val != "":
                        val_set.add(val.strip())  # Remove all spaces

                # Check that all misspellings are different from the original
                #
                if key in val_set:
                    print(
                        "Error: A misspelling is the same as the original value"
                        + ' "%s" in line: "%s"' % (key, l)
                    )
                    raise Exception

                # Now insert into misspellings dictionary
                #
                key_val_set = misspell_dict.get(key, set())
                key_val_set = key_val_set.union(val_set)
                misspell_dict[key] = key_val_set

            elif len(ll) == 1:  # Line contains only values - - - - - - - - - - - -

                if key == None:
                    print('Error: No key (correct word) defined in line: "%s"' % (l))
                    raise Exception

                vals = ll[0].lower()  # Get values in a string
                val_list = vals.split(",")

                val_set = set()
                for val in val_list:
                    if val != "":
                        val_set.add(val.strip())  # Remove all spaces

                # Check that all misspellings are different from the original
                #
                if key in val_set:
                    print(
                        "Error: A misspelling is the same as the original value"
                        + ' "%s" in line: "%s"' % (key, l)
                    )
                    raise Exception

                # Now insert into misspellings dictionary
                #
                key_val_set = misspell_dict.get(key, set())
                key_val_set = key_val_set.union(val_set)
                misspell_dict[key] = key_val_set

            else:
                print('error:Illegal line format in line: "%s"' % (l))
                raise Exception

    # Now convert all sets into lists - - - - - - - - - - - - - - - - - - - - -
    #
    for k in misspell_dict:
        misspell_dict[k] = list(misspell_dict[k])

    # print '  Length of misspellings dictionary: %d' % (len(misspell_dict))

    return misspell_dict


# -----------------------------------------------------------------------------


def load_lookup_dict(dict_file_name):
    """Load a look-up table
  """

    # Open file and read all lines into a list
    #
    try:
        f = open(dict_file_name, "r", encoding="utf8")
    except:
        print('Error: Can not read from lookup file "%s"' % (dict_file_name))
        raise IOError

    file_data = f.readlines()  # Read complete file
    f.close()

    lookup_dict = {}

    key = None  # Start with a non-existing key word (correct word)

    # Now process all lines - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    for line in file_data:
        l = line.strip()  # Remove line separators

        if (len(l) > 0) and (l[0] != "#"):  # Not empty line and not comment

            ll = l.split(":")  # Separate key from values

            if (ll[0] == "") and (len(ll) > 1):
                ll = ll[1:]

            if len(ll) == 2:  # Line contains a key - - - - - - - - - - - - - - - -

                key = ll[0].strip().lower()  # Get key, make lower and strip spaces

                if key == "":
                    print('This should not happen: "%s"' % (l))
                    raise Exception

                vals = ll[1].strip().lower()  # Get values in a string

                if vals == "":
                    print(
                        'Error: No lookupings given for "%s" in line: "%s"' % (key, l)
                    )
                    raise Exception

                val_list = vals.split(",")
                val_set = set()
                tmp_list = []
                freq_flag = False
                for val in val_list:
                    if val.find(";") > -1:
                        freq_flag = True
                        vl = val.split(";")
                        for i in range(int(vl[1])):
                            tmp_list.insert(i, vl[0].strip())
                        lookup_dict[key] = tmp_list
                    else:
                        if val != "":
                            val_set.add(val.strip())  # Remove all spaces

                if not freq_flag:
                    # Now insert into lookup dictionary
                    #
                    key_val_set = lookup_dict.get(key, set())
                    key_val_set = key_val_set.union(val_set)
                    lookup_dict[key] = key_val_set

            elif len(ll) == 1:  # Line contains only values - - - - - - - - - - - -

                if key == None:
                    print('Error: No key (correct word) defined in line: "%s"' % (l))
                    raise Exception

                vals = ll[0].lower()  # Get values in a string
                val_list = vals.split(",")
                val_set = set()
                tmp_list = []
                freq_flag = False
                for val in val_list:
                    if val.find(";") > -1:
                        freq_flag = True
                        vl = val.split(";")
                        for i in range(int(vl[1])):
                            tmp_list.insert(i, vl[0].strip())
                        lookup_dict[key] = tmp_list
                    else:
                        if val != "":
                            val_set.add(val.strip())  # Remove all spaces
                if not freq_flag:
                    # Now insert into lookupings dictionary
                    #
                    key_val_set = lookup_dict.get(key, set())
                    key_val_set = key_val_set.union(val_set)
                    lookup_dict[key] = key_val_set

            else:
                print('error:Illegal line format in line: "%s"' % (l))
                raise Exception

    # Now convert all sets into lists - - - - - - - - - - - - - - - - - - - - -
    #
    for k in lookup_dict:
        lookup_dict[k] = list(lookup_dict[k])

    return lookup_dict


# -----------------------------------------------------------------------------


def random_select(prob_dist_list):
    """Randomly select one of the list entries (tuples of value and probability
     values).
  """

    rand_num = random.random()  # Random number between 0.0 and 1.0

    ind = -1
    while prob_dist_list[ind][1] > rand_num:
        ind -= 1

    return prob_dist_list[ind][0]


# =============================================================================
# Functions for phonetic and OCR transformation
# Agus Pudjijono, 2008


def get_transformation(s, t):
    if s == "":
        return s

    changesstr2 = ""

    def slavo_germanic(str):
        if (
            (str.find("w") > -1)
            or (str.find("k") > -1)
            or (str.find("cz") > -1)
            or (str.find("witz") > -1)
        ):
            return 1
        else:
            return 0

    # Function which replaces a pattern in a string - - - - - - - - - - - - - - -
    # - 'where' can be one of: 'ALL','START','END','MIDDLE'
    # - Pre-condition (default 'None') can be 'V' for vowel or 'C' for consonant
    # - Post-condition (default 'None') can be 'V' for vowel or 'C' for consonant
    #
    def do_collect_replacement(s, where, orgpat, newpat, precond, postcond, existcond, startcond  ):
        vowels = "aeiouy"
        tmpstr = s
        changesstr = ""

        start_search = 0  # Position from where to start the search
        pat_len = len(orgpat)
        stop = False

        # As long as pattern is in string
        #
        while (orgpat in tmpstr[start_search:]) and (stop == False):

            pat_start = tmpstr.find(orgpat, start_search)
            str_len = len(tmpstr)

            # Check conditions of previous and following character
            #
            OKpre = False  # Previous character condition
            OKpre1 = False  # Previous character1 condition
            OKpre2 = False  # Previous character2 condition

            OKpost = False  # Following character condition
            OKpost1 = False  # Following character1 condition
            OKpost2 = False  # Following character2 condition

            OKexist = False  # Existing pattern condition
            OKstart = False  # Existing start pattern condition

            index = 0

            if precond == "None":
                OKpre = True

            elif pat_start > 0:
                if ((precond == "V") and (tmpstr[pat_start - 1] in vowels)) or (
                    (precond == "C") and (tmpstr[pat_start - 1] not in vowels)
                ):
                    OKpre = True

                elif (precond.find(";")) > -1:
                    if precond.find("|") > -1:
                        rls = precond.split("|")

                        rl1 = rls[0].split(";")

                        if int(rl1[1]) < 0:
                            index = pat_start + int(rl1[1])
                        else:
                            index = pat_start + (len(orgpat) - 1) + int(rl1[1])

                        i = 2
                        if rl1[0] == "n":
                            while i < (len(rl1)):
                                if tmpstr[index : (index + len(rl1[i]))] == rl1[i]:
                                    OKpre1 = False
                                    break
                                else:
                                    OKpre1 = True
                                i += 1
                        else:
                            while i < (len(rl1)):
                                if tmpstr[index : (index + len(rl1[i]))] == rl1[i]:
                                    OKpre1 = True
                                    break
                                i += 1

                        rl2 = rls[1].split(";")

                        if int(rl2[1]) < 0:
                            index = pat_start + int(rl2[1])
                        else:
                            index = pat_start + (len(orgpat) - 1) + int(rl2[1])

                        i = 2
                        if rl2[0] == "n":
                            while i < (len(rl2)):
                                if tmpstr[index : (index + len(rl2[i]))] == rl2[i]:
                                    OKpre2 = False
                                    break
                                else:
                                    OKpre2 = True
                                i += 1
                        else:
                            while i < (len(rl2)):
                                if tmpstr[index : (index + len(rl2[i]))] == rl2[i]:
                                    OKpre2 = True
                                    break
                                i += 1

                        OKpre = OKpre1 and OKpre2

                    else:
                        rl = precond.split(";")
                        # -
                        if int(rl[1]) < 0:
                            index = pat_start + int(rl[1])
                        else:
                            index = pat_start + (len(orgpat) - 1) + int(rl[1])

                        i = 2
                        if rl[0] == "n":
                            while i < (len(rl)):
                                if tmpstr[index : (index + len(rl[i]))] == rl[i]:
                                    OKpre = False
                                    break
                                else:
                                    OKpre = True
                                i += 1
                        else:
                            while i < (len(rl)):
                                if tmpstr[index : (index + len(rl[i]))] == rl[i]:
                                    OKpre = True
                                    break
                                i += 1

            if postcond == "None":
                OKpost = True

            else:
                pat_end = pat_start + pat_len

                if pat_end < str_len:
                    if ((postcond == "V") and (tmpstr[pat_end] in vowels)) or (
                        (postcond == "C") and (tmpstr[pat_end] not in vowels)
                    ):
                        OKpost = True
                    elif (postcond.find(";")) > -1:
                        if postcond.find("|") > -1:
                            rls = postcond.split("|")

                            rl1 = rls[0].split(";")

                            if int(rl1[1]) < 0:
                                index = pat_start + int(rl1[1])
                            else:
                                index = pat_start + (len(orgpat) - 1) + int(rl1[1])

                            i = 2
                            if rl1[0] == "n":
                                while i < (len(rl1)):
                                    if tmpstr[index : (index + len(rl1[i]))] == rl1[i]:
                                        OKpost1 = False
                                        break
                                    else:
                                        OKpost1 = True
                                    i += 1
                            else:
                                while i < (len(rl1)):
                                    if tmpstr[index : (index + len(rl1[i]))] == rl1[i]:
                                        OKpost1 = True
                                        break
                                    i += 1

                            rl2 = rls[1].split(";")

                            if int(rl2[1]) < 0:
                                index = pat_start + int(rl2[1])
                            else:
                                index = pat_start + (len(orgpat) - 1) + int(rl2[1])

                            i = 2
                            if rl2[0] == "n":
                                while i < (len(rl2)):
                                    if tmpstr[index : (index + len(rl2[i]))] == rl2[i]:
                                        OKpost2 = False
                                        break
                                    else:
                                        OKpost2 = True
                                    i += 1
                            else:
                                while i < (len(rl2)):
                                    if tmpstr[index : (index + len(rl2[i]))] == rl2[i]:
                                        OKpost2 = True
                                        break
                                    i += 1

                            OKpost = OKpost1 and OKpost2

                        else:
                            rl = postcond.split(";")

                            if int(rl[1]) < 0:
                                index = pat_start + int(rl[1])
                            else:
                                index = pat_start + (len(orgpat) - 1) + int(rl[1])

                            i = 2
                            if rl[0] == "n":
                                while i < (len(rl)):
                                    if tmpstr[index : (index + len(rl[i]))] == rl[i]:
                                        OKpost = False
                                        break
                                    else:
                                        OKpost = True
                                    i += 1
                            else:
                                while i < (len(rl)):
                                    if tmpstr[index : (index + len(rl[i]))] == rl[i]:
                                        OKpost = True
                                        break
                                    i += 1

            if existcond == "None":
                OKexist = True

            else:
                rl = existcond.split(";")
                if rl[1] == "slavo":
                    r = slavo_germanic(s)
                    if rl[0] == "n":
                        if r == 0:
                            OKexist = True
                    else:
                        if r == 1:
                            OKexist = True
                else:
                    i = 1
                    if rl[0] == "n":
                        while i < (len(rl)):
                            if s.find(rl[i]) > -1:
                                OKexist = False
                                break
                            else:
                                OKexist = True
                            i += i
                    else:
                        while i < (len(rl)):
                            if s.find(rl[i]) > -1:
                                OKexist = True
                                break
                            i += i

            if startcond == "None":
                OKstart = True

            else:
                rl = startcond.split(";")
                i = 1
                if rl[0] == "n":
                    while i < (len(rl)):
                        if s.find(rl[i]) > -1:
                            OKstart = False
                            break
                        else:
                            OKstart = True
                        i += i
                else:
                    while i < (len(rl)):
                        if s.find(rl[i]) == 0:
                            OKstart = True
                            break
                        i += i

            # Replace pattern if conditions and position OK
            #
            if (
                (OKpre == True)
                and (OKpost == True)
                and (OKexist == True)
                and (OKstart == True)
            ) and (
                ((where == "START") and (pat_start == 0))
                or (
                    (where == "MIDDLE")
                    and (pat_start > 0)
                    and (pat_start + pat_len < str_len)
                )
                or ((where == "END") and (pat_start + pat_len == str_len))
                or (where == "ALL")
            ):
                tmpstr = tmpstr[:pat_start] + newpat + tmpstr[pat_start + pat_len :]
                changesstr += "," + orgpat + ">" + newpat + ">" + where.lower()
                start_search = pat_start + len(newpat)

            else:
                start_search = pat_start + 1

            if start_search >= (len(tmpstr) - 1):
                stop = True

        tmpstr += changesstr
        return tmpstr

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    # Load the replacement table

    this_dir, this_filename = os.path.split(__file__)

    if t == "pho":
        # replace_table_file_name= 'config'+os.sep+'lib_phonetic_rules.txt'
        replace_table_file_name = os.path.join(this_dir, "config", phonetic_rules_file)

    elif t == "ocr":
        # replace_table_file_name= 'config'+os.sep+'lib_ocr_rules.txt'
        replace_table_file_name = os.path.join(this_dir, "config", ocr_rules_file)

    try:
        f = open(replace_table_file_name, "r")
    except:
        print("Error cannot read file %s" % (replace_table_file_name))
        raise IOError

    file_data = f.readlines()
    f.close()

    replace_table = []
    numrule = 1
    for line in file_data:
        val_tuple = ()
        l = line.strip()
        val_list = l.split(",")
        for val in val_list:
            if val != "":
                val = val.strip()
                val_tuple += (val,)
        replace_table.insert(numrule, val_tuple)
        numrule += 1

    workstr = s

    for rtpl in replace_table:  # Check all transformations in the table
        if len(rtpl) == 3:
            rtpl += ("None", "None", "None", "None")

        workstr = do_collect_replacement(
            s, rtpl[0], rtpl[1], rtpl[2], rtpl[3], rtpl[4], rtpl[5], rtpl[6]
        )
        if workstr.find(",") > -1:
            tmpstr = workstr.split(",")
            workstr = tmpstr[0]
            if changesstr2.find(tmpstr[1]) == -1:
                changesstr2 += tmpstr[1] + ";"
    workstr += "," + changesstr2

    return workstr


# -----------------------------------------------------------------------------


def apply_change(str_to_change, ch):

    workstr = str_to_change
    list_ch = ch.split(">")
    subs = list_ch[1]
    if list_ch[1] == "@":  # @ is blank
        subs = ""
    tmpstr = workstr
    org_pat_length = len(list_ch[0])
    str_length = len(workstr)

    if list_ch[2] == "end":
        org_pat_start = workstr.find(list_ch[0], str_length - org_pat_length)
    elif list_ch[2] == "middle":
        org_pat_start = workstr.find(list_ch[0], 1)
    else:  # start and all
        org_pat_start = workstr.find(list_ch[0], 0)

    if org_pat_start == 0:
        workstr = subs + workstr[org_pat_length:]
    elif org_pat_start > 0:
        workstr = (
            workstr[0:org_pat_start] + subs + workstr[org_pat_start + org_pat_length :]
        )

    if workstr == tmpstr:
        workstr = str_to_change

    return workstr
