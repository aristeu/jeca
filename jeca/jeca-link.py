# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import getopt
import sys
import time
from jira import JIRA
from jeca.output import formatted_output

# we implement these manually
available_fields = ['key', 'name', 'type', 'relation', 'status']
default_fields = ['key', 'relation', 'type', 'status']
# list ######
def op_list(config, jirainst, opts, args):
    fields = default_fields
    issue = None
    for option,value in opts:
        if option == '--fields' or option == '-f':
            fields = value.split(',')
        elif option == '-j':
            issue = value
        else:
            sys.stderr.write("Unknown option: %s\n" % option)
            usage(sys.stderr)
            sys.exit(2)

    if issue is None:
        op_list_usage(sys.stderr)
        sys.exit(1)

    jql = "key = %s" % issue
    try:
        results = jirainst.search_issues(jql_str = jql, fields = ['issuelinks'], maxResults = 1, validate_query = True)
    except JIRAError as http_err:
        if http_err.status_code == 429:
            time.sleep(1)
            results = jirainst.search_issues(jql_str = jql, fields = ['issuelinks'], maxResults = 1, validate_query = True)

    output = []
    for li in results:
        l = li.raw['fields']['issuelinks']
        for issuelink in l:
            line = []
            for f in fields:
                if 'inwardIssue' in issuelink:
                    task = issuelink['inwardIssue']
                    direction = 'inward'
                else:
                    task = issuelink['outwardIssue']
                    direction = 'outward'

                if f == 'key':
                   line.append(task['key'])
                elif f == 'relation':
                    line.append(issuelink['type'][direction])
                elif f == 'type':
                    line.append(task['fields']['issuetype']['name'])
                elif f == 'status':
                    line.append(task['fields']['status']['name'])
                elif f == 'name':
                    line.append(task['fields']['summary'])
            output.append(line)
    formatted_output(output)

    return 0

def op_list_usage(f):
    f.write("jeca %s list <-j <jira id>> [-f <fields>] [-h|--help]\n\n" % MODULE_NAME)
    f.write("-h|--help\t\tthis message\n")
# list ######

MODULE_NAME = "link"
MODULE_OPERATIONS = { "list": op_list }
MODULE_OPERATION_USAGE = { "list": op_list_usage }
MODULE_OPERATION_SHORT_OPTIONS = { "list": "j:f:" }
MODULE_OPERATION_LONG_OPTIONS = { "list": ["fields="] }
MODULE_OPERATION_REQUIRED_ARGS = { "list": 0 }

def list_operations(f):
    for op in MODULE_OPERATIONS:
        f.write("\t%s\n" % op)

def jeca_module_main(config, jirainst, argv):
    if len(argv) < 2:
        print("%s <operation>" % MODULE_NAME)
        print("Available operations:")
        list_operations(sys.stdout)
        sys.exit(0)
    if argv[1] not in MODULE_OPERATIONS:
        sys.stderr.write("Invalid operation: %s\n" % argv[1])
        sys.stderr.write("Available operations:\n")
        list_operations(sys.stderr)
        sys.exit(2)

    operation = argv[1]
    short_options = MODULE_OPERATION_SHORT_OPTIONS[operation]
    long_options = MODULE_OPERATION_LONG_OPTIONS[operation]
    short_options += "h"
    long_options.append("help")

    try:
        opts, args = getopt.getopt(argv[2:], short_options, long_options)
    except getopt.GetoptError as err:
        sys.stderr.write("%s\n" % err)
        MODULE_OPERATION_USAGE[operation](sys.stderr)
        sys.exit(2)
    for o,v in opts:
        if o == "-h" or o == "--help":
            MODULE_OPERATION_USAGE[operation](sys.stdout)
            sys.exit(0)
    if len(args) < MODULE_OPERATION_REQUIRED_ARGS[operation]:
        sys.stderr.write("Not enough arguments\n")
        MODULE_OPERATION_USAGE[operation](sys.stderr)
        sys.exit(2)

    return MODULE_OPERATIONS[operation](config, jirainst, opts, args)

