#-*- coding: utf-8 -*-
import sys, getopt
import json
import csv
import datetime
from checks import *
from models import Sites, SiteTests
import config

def testsites(sites, test_type=None, show_reviews=False, only_test_untested_last_hours=24, order_by='title ASC'):
    """
    Executing the actual tests.
    Attributes:
    * test_type=num|None to execute all available tests
    """

    result = list()

    # TODO: implementera test_type=None

    print("###############################################")

    i = 1

    print('Webbadresser som testas:', len(sites))

    for site in sites:
        site_id = site[0]
        website = site[1]
        print('{}. Testar adress {}'.format(i, website))
        the_test_result = None

        try:
            if test_type == 2:
                the_test_result = check_four_o_four(website)
            elif test_type == 6:
                the_test_result = check_w3c_valid(website)
            elif test_type == 7:
                the_test_result = check_w3c_valid_css(website)
            elif test_type == 20:
                the_test_result = check_privacy_webbkollen(website)
            elif test_type == 0:
                the_test_result = check_google_pagespeed(website)

            if the_test_result != None:
                print('Rating: ', the_test_result[0])
                if show_reviews:
                    print('Review:\n', the_test_result[1])

                json_data = ''
                try:
                    json_data = the_test_result[2]
                except:
                    json_data = ''
                    pass

                checkreport = str(the_test_result[1]).encode('utf-8') # för att lösa encoding-probs
                jsondata = str(json_data).encode('utf-8') # --//--

                site_test = SiteTests(site_id=site_id, type_of_test=test_type, check_report=checkreport, rating=the_test_result[0], test_date=datetime.datetime.now(), json_check_data=jsondata).todata()

                result.append(site_test)

                the_test_result = None # 190506 för att inte skriva testresultat till sajter när testet kraschat. Måste det sättas till ''?
        except Exception as e:
            print('FAIL!', website, '\n', e)
            pass

        i += 1
    
    return result

def testing(sites, test_type= TEST_ALL, show_reviews= False):
    print('### {0} ###'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    tests = list()
    ##############
    if (test_type == TEST_ALL or test_type == TEST_GOOGLE_PAGESPEED):
        print('###############################\nKör test: 0 - Google Pagespeed')
        tests.extend(testsites(sites, test_type=TEST_GOOGLE_PAGESPEED, show_reviews=show_reviews))
    if (test_type == TEST_ALL or test_type == TEST_PAGE_NOT_FOUND):
        print('###############################\nKör test: 2 - 404-test')
        tests.extend(testsites(sites, test_type=TEST_PAGE_NOT_FOUND, show_reviews=show_reviews))
    if (test_type == TEST_ALL or test_type == TEST_HTML):
        print('###############################\nKör test: 6 - HTML')
        tests.extend(testsites(sites, test_type=TEST_HTML, show_reviews=show_reviews))
    if (test_type == TEST_ALL or test_type == TEST_CSS):
        print('###############################\nKör test: 7 - CSS')
        tests.extend(testsites(sites, test_type=TEST_CSS, show_reviews=show_reviews))
    if (test_type == TEST_ALL or test_type == TEST_WEBBKOLL):
        print('###############################\nKör test: 20 - Webbkoll')
        tests.extend(testsites(sites, test_type=TEST_WEBBKOLL, show_reviews=show_reviews))
    return tests

def validate_test_type(test_type):
    if test_type != TEST_HTML and test_type != TEST_PAGE_NOT_FOUND and test_type != TEST_CSS and test_type != TEST_WEBBKOLL and test_type != TEST_GOOGLE_PAGESPEED:
        print('Valid arguments for option -t/--test:')
        print('-t 0\t: Google Pagespeed')
        print('-t 2\t: 404-test')
        print('-t 6\t: HTML')
        print('-t 7\t: CSS')
        print('-t 20\t: Webbkoll')
        return -2
    else:
        return test_type

def main(argv):
    """
    WebPerf Core

    Usage:
    default.py -u https://webperf.se

    Options and arguments:
    -h/--help\t\t\t: Help information on how to use script
    -u/--url <site url>\t\t: website url to test against
    -t/--test <0/2/6/7/20>\t: runs ONE specific test against website(s)
    -r/--review\t\t\t: show reviews in terminal
    -i/--input <file path>\t: input file path (.json)
    -o/--output <file path>\t: output file path (.json/.csv/.sql)
    """

    test_type = TEST_ALL
    sites = list()
    output_filename = ''
    show_reviews = False

    try:
        opts, args = getopt.getopt(argv,"hu:t:i:o:r",["help","url","test", "input", "output", "review", "report"])
    except getopt.GetoptError:
        print(main.__doc__)
        sys.exit(2)

    if (opts.__len__() == 0):
        print(main.__doc__)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'): # help
            print(main.__doc__)
            sys.exit()
        elif opt in ("-u", "--url"): # site url
            sites.append([0, arg])
        elif opt in ("-t", "--test"): # test type
            try:
                tmp_test_type = int(arg)
                test_type = validate_test_type(tmp_test_type)
                if test_type == -2:
                    sys.exit(2)
            except Exception:
                validate_test_type(arg)
                sys.exit(2)
        elif opt in ("-i", "--input"): # input file path
            with open(arg) as json_input_file:
                data = json.load(json_input_file)
                for site in data["sites"]:
                    sites.append([site["id"], site["url"]])
            pass
        elif opt in ("-o", "--output"): # output file path
            output_filename = arg
            pass
        elif opt in ("-r", "--review", "--report"): # writes reviews directly in terminal
            show_reviews = True
            pass

    if (len(sites)):
        siteTests = testing(sites, test_type=test_type, show_reviews=show_reviews)
        if (len(output_filename) > 0):
            file_ending = output_filename[-4:].lower()
            if (file_ending == ".csv"):
                with open(output_filename, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=SiteTests.fieldnames())

                    writer.writeheader()
                    writer.writerows(siteTests)
            elif file_ending == ".sql":
                with open(output_filename, 'w') as outfile:
                                
                    for test in siteTests:
                        format_str = """INSERT INTO sitetests (site_id, test_date, type_of_test, check_report, json_check_data, most_recent, rating)
                        VALUES ("{siteid}", "{testdate}", "{testtype}", "{report}", "{json}", "{recent}", "{rating}");\n"""
                        sql_command = format_str.format(siteid=test["site_id"], testdate=test["date"], testtype=test["type_of_test"], report=test["report"], json=test["data"], recent=1, rating=test["rating"])
                    
                        outfile.write(sql_command)
            else:
                with open(output_filename, 'w') as outfile:
                    # json require us to have an object as root element
                    testsContainerObject = {
                        "tests": siteTests
                    }
                    json.dump(testsContainerObject, outfile)
    else:
        print(main.__doc__)


"""
If file is executed on itself then call a definition, mostly for testing purposes
"""
if __name__ == '__main__':
    main(sys.argv[1:])