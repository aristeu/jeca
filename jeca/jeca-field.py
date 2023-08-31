# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import getopt
import sys
import re
from atlassian import Jira

# list ######
all_columns = ['id', 'name', 'custom', 'orderable', 'navigable', 'searchable', 'customId']
default_columns = [ 'id', 'name' ]
def op_list(config, jirainst, opts, args):
    columns= []
    default = True
    custom = True
    for (opt, arg) in opts:
        if opt == '-f' or opt == '--fields':
            columns = arg.split(',')
            for c in columns:
                if c not in all_columns:
                    sys.stderr.write("Invalid field: %s\n" % c)
                    sys.exit(1)
        elif opt == '--nocustom':
            custom = False
        elif opt == '--nodefault':
            default = False

    if len(columns) == 0:
        columns = default_columns

    for f in jirainst.fields():
        if custom == False and f['custom'] == True:
            continue
        if default == False and f['custom'] == False:
            continue

        line = []
        for c in columns:
            if c in f:
                line.append(str(f[c]))
            else:
                line.append('')
        if len(line) > 0:
            sys.stdout.write("%s\n" % '\t'.join(line))

    return 0

def op_list_usage(f):
    f.write("jeca field list [-f <fields>] [-h|--help]\n\n")
    f.write("-f,--fields <fields>\t\tspecify which fields of fields to show\n")
    f.write("--nocustom\t\tDon't print custom fields\n")
    f.write("--nodefault\t\tDon't print Jira's default fields\n")
    f.write("-h|--help\t\tthis message\n\n")
    f.write("Available fields: %s\n" % ', '.join(all_columns))
# list ######

MODULE_NAME = "field"
MODULE_OPERATIONS = { "list": op_list }
MODULE_OPERATION_USAGE = { "list": op_list_usage }
MODULE_OPERATION_SHORT_OPTIONS = { "list": "f:" }
MODULE_OPERATION_LONG_OPTIONS = { "list": ["fields=", "nocustom", "nodefault"] }
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

