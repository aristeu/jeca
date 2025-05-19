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
import configparser
from atlassian import Jira
from jeca.output import formatted_output
from jeca.field import field_cache, field_cache_get_allowed
from jeca.alias import alias_translate

# list ######
all_columns = ['id', 'name', 'custom', 'orderable', 'navigable', 'searchable', 'customId', 'clauseNames', 'schema']
default_columns = [ 'id', 'name' ]
def op_list(config, jirainst, opts, args):
    columns = default_columns
    default = True
    custom = True
    for (opt, arg) in opts:
        if opt == '-f' or opt == '--fields':
            if arg == 'all':
                columns = all_columns
            else:
                columns = arg.split(',')
                for c in columns:
                    if c not in all_columns:
                        sys.stderr.write("Invalid field: %s\n" % c)
                        sys.exit(1)
        elif opt == '--nocustom':
            custom = False
        elif opt == '--nodefault':
            default = False
        else:
            sys.stderr.write("Unknown option: %s\n" % option)
            op_list_usage(sys.stderr)
            sys.exit(1)

    results = []
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
        results.append(line)

    formatted_output(results)

    return 0

def op_list_usage(f):
    f.write("jeca field list [-f <fields>] [-h|--help]\n\n")
    f.write("-f,--fields <fields>\t\tspecify which fields of fields to show\n")
    f.write("--nocustom\t\tDon't print custom fields\n")
    f.write("--nodefault\t\tDon't print Jira's default fields\n")
    f.write("-h|--help\t\tthis message\n\n")
    f.write("Available fields: %s\n" % ', '.join(all_columns))
# list ######

# cache #####
def op_cache(config, jirainst, opts, args):
    if len(args) == 0:
        op_cache_usage(sys.stderr)
        return 1

    issue = args[0]
    return field_cache(config, jirainst, issue)

def op_cache_usage(f):
    f.write("jeca field cache [<issue>] [-h|--help]\n\n")
    f.write("<issue> is used as reference because fields are reported per issue\n")

# cache #####

# allowed ###
def op_allowed(config, jirainst, opts, args):
    if len(args) == 0:
        op_allowed_usage(sys.stderr)
        return 1

    field = alias_translate(config, args[0])
    allowed = field_cache_get_allowed(config, jirainst, field)
    if allowed is None:
        sys.stdout.write("Unable to find field in the cache. Running 'jeca field cache' is recommended\n")
        return 1
    if len(allowed) == 0:
        return 0
    for i in str(allowed).split(','):
        print(i)
    return 0

def op_allowed_usage(f):
    f.write("jeca field allowed [<field>] [-h|--help]\n\n")
    f.write("<field> might be an alias or field name\n")
# allowed ###

MODULE_NAME = "field"
MODULE_OPERATIONS = { "list": op_list, "cache": op_cache, "allowed": op_allowed }
MODULE_OPERATION_USAGE = { "list": op_list_usage, "cache": op_cache_usage, "allowed": op_allowed_usage }
MODULE_OPERATION_SHORT_OPTIONS = { "list": "f:", "cache": "", "allowed": "" }
MODULE_OPERATION_LONG_OPTIONS = { "list": ["fields=", "nocustom", "nodefault"], "cache": [], "allowed": [] }
MODULE_OPERATION_REQUIRED_ARGS = { "list": 0, "cache": 1, "allowed": 1 }

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

