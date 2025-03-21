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
from jeca.output import formatted_output

# list ######
available_fields = [ 'id', 'name', 'description', 'owner', 'jql', 'viewUrl', 'favourite', 'sharePermissions', 'editable', 'sharedUsers', 'subscriptions' ]
default_fields = ['name']
def op_list(config, jirainst, opts, args):
    fields = default_fields
    if 'filter' in config and 'default_fields' in config['filter']:
        fields = config['filter']['default_fields']

    for option,value in opts:
        if option == '--fields' or option == '-f':
            if value == 'all':
                fields = available_fields
            else:
                for f in value.split(','):
                    if f not in available_fields:
                        sys.stderr.write("Field %s not available (%s)\n" % (f, ','.join(available_fields)))
                        sys.exit(1)
                    fields = value.split(',')

    results = []
    for f in jirainst.favourite_filters():
        line = []
        for c in fields:
            line.append(str(f.raw[c]))
        results.append(line)

    formatted_output(results)

    return 0

def op_list_usage(f):
    f.write("jeca %s list [-f <list>|--fields <list>][-h|--help]\n\n" % MODULE_NAME)
    f.write("Lists the *favourite* filters. There isn't a way to list or search filters\n\n")
    f.write("-f|--fields <list>\tDefine which fields will be listed\n")
    f.write("-h|--help\t\tthis message\n")
# list ######

# set #######
set_field_list = ['name', 'description', 'jql', 'favourite']
def op_set(config, jirainst, opts, args):
    field = None
    value = None
    f = None
    arg_list = {}
    for option,v in opts:
        if option == '--field' or option == '-f':
            if v not in set_field_list:
                op_set_usage(sys.stderr)
                return 1
            field = v
        elif option == '--value' or option == '-v':
            value = v
        elif option == '--filter' or option == '-F':
            f = v

    arg_list['filter_id'] = f
    arg_list[field] = value

    if field is None or value is None or f is None:
        op_set_usage(sys.stderr)
        return 1

    jirainst.update_filter(**arg_list)

    return 0

def op_set_usage(f):
    f.write("jeca %s set <-F <name>> <--field <name> <--value <value>>[-h|--help]\n\n" % MODULE_NAME)
    f.write("-F|--filter <name>\t\tName of the filter that will be updated\n")
    f.write("-f|--field <name>\t\tName of the field to be changed\n")
    f.write("-v|--value <value>\t\tNew value of the field\n")
    f.write("\nField list: %s\n" % ','.join(set_field_list))
    f.write("\nWARNING: keep in mind setting a filter as favourite over REST is not supported yet if you're not the filter owner\n")
    f.write("-h|--help\t\tthis message\n")

# set #######

MODULE_NAME = "filter"
MODULE_OPERATIONS = { "list": op_list, "set": op_set }
MODULE_OPERATION_USAGE = { "list": op_list_usage, "set": op_set_usage }
MODULE_OPERATION_SHORT_OPTIONS = { "list": "f:", "set": "F:f:v:" }
MODULE_OPERATION_LONG_OPTIONS = { "list": ["fields="], "set": ["filter=", "field=", "value="] }
MODULE_OPERATION_REQUIRED_ARGS = { "list": 0, "set": 0 }

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

