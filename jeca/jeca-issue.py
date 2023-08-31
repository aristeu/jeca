# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import getopt
import sys
from jira import JIRA
from jeca.alias import alias_translate

# jira.search_issues()
# jql_str (str)					 The JQL search string.
# startAt (int)					 Index of the first issue to return. (Default: 0)
# maxResults (int)				 Maximum number of issues to return. Total number of results is available in the total attribute of the returned ResultList. If maxResults evaluates to False, it will try to get all issues in batches. (Default: 50)
# validate_query (bool)				 True to validate the query. (Default: True)
# fields (Optional[Union[str, List[str]]])	 comma-separated string or list of issue fields to include in the results. Default is to include all fields.
# expand (Optional[str])			 extra information to fetch inside each resource
# properties (Optional[str])			 extra properties to fetch inside each result
# json_result (bool)				 True to return a JSON response. When set to False a ResultList will be returned. (Default: False)

# assignee = currentuser()

# list ######
default_filter = [ 'assignee = currentuser()' ]
default_fields = [ 'key', 'summary' ]
def op_list(config, jirainst, opts, args):
    try:
        default_project = config['jira']['default_project']
        default_filter.append("project = %s" % default_project)
    except:
        pass
        default_project = ""

    fields = []
    jql = ""
    search_filter = []
    for option,value in opts:
        if option == '--fields' or option == '-f':
            fields_input = value.split(',')
            for f in fields_input:
                fields.append(alias_translate(config, f))
        elif option == '--project' or option == '-p':
            search_filter.append("project = %s" % value)
        elif option == '--assignee' or option == '-a':
            search_filter.append("assignee = \"%s\"" % value)
        elif option == '--jql':
            jql = value
        else:
            sys.stderr.write("Unknown option: %s\n" % option)
            usage(sys.stderr)
            sys.exit(2)

    if len(fields) == 0:
        # first look if we have a configuration for this
        try:
            fields = config['issue-list']['default_fields'].split(',')
        except:
            pass
            fields = default_fields

    if len(jql) == 0:
        if len(search_filter) == 0:
            try:
                jql = config['issue-list']['default_jql']
            except:
                pass
                jql = " and ".join(default_filter)
        else:
            try:
                search_filter.remove("project = all")
            except:
                pass
            jql = " and ".join(search_filter)


    # FIXME: maxResults should be a config
    try:
        result = jirainst.search_issues(jql_str = jql, fields = ','.join(fields), maxResults = 500, validate_query = True)
    except Exception as ex:
        sys.stderr.write("Error executing search: %s\n" % str(ex))
        sys.exit(2)

    for issue in result:
        newline = True
        for f in fields:
            if not newline:
                sys.stdout.write("\t")
            newline = False
            # sigh
            if f == 'key':
                sys.stdout.write(issue.key)
            else:
                # if the project doesn't have a certain field, it won't return
                # anything. If the field exists but it's not set, it'll return
                # "None"
                try:
                    sys.stdout.write(str(issue.get_field(f)))
                except:
                    sys.stdout.write('NotDefined')
        sys.stdout.write("\n")

    return 0

def op_list_usage(f):
    f.write("jeca %s list [-h|--help]\n\n" % MODULE_NAME)
    f.write("-f,--field <fields>\tspecify the fields shown\n")
    f.write("-p,--project <project>\tfilter by project\n")
    f.write("-a,--assignee <user>\tfilter by assignee\n")
    f.write("--jql <JQL query>\tspecify the JQL query manually\n")
    f.write("-h|--help\t\tthis message\n")
# list ######

MODULE_NAME = "issue"
MODULE_OPERATIONS = { "list": op_list }
MODULE_OPERATION_USAGE = { "list": op_list_usage }
MODULE_OPERATION_SHORT_OPTIONS = { "list": "f:p:a:" }
MODULE_OPERATION_LONG_OPTIONS = { "list": ["fields=", "project=", "assignee=", "jql="] }
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

