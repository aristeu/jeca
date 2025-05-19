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

# list ######
available_fields = ['id', 'name']
default_fields = ['name']
def op_list(config, jirainst, opts, args):
    fields = default_fields
    for option,value in opts:
        if option == '--fields' or option == '-f':
            if value == 'all':
                fields = available_fields
            else:
                fields = value.split(',')
                for f in fields:
                    if f not in available_fields:
                        sys.stderr.write("Field %s not available (%s)\n", (f, ','.join(available_fields)))
                        sys.exit(1)
        else:
            sys.stderr.write("Unknown option: %s\n" % option)
            op_list_usage(sys.stderr)
            sys.exit(2)

    sprints = []
    count = 0;
    output = []
    while True:
        sprints = jirainst.sprints(maxResults=50, startAt=count, board_id=args[0])
        for s in sprints:
            line = []
            for f in fields:
                line.append(str(s.raw[f]))
            count = count + 50
            output.append('\t'.join(line))

        if len(sprints) <  50:
            break
    if len(output) > 0:
        print('\n'.join(output))

    return 0

def op_list_usage(f):
    f.write("jeca %s list [-f <fields>] <board> | [-h|--help]\n\n" % MODULE_NAME)
    f.write("-h|--help\t\tthis message\n")
# list ######

MODULE_NAME = "sprint"
MODULE_OPERATIONS = { "list": op_list }
MODULE_OPERATION_USAGE = { "list": op_list_usage, }
MODULE_OPERATION_SHORT_OPTIONS = { "list": "f:" }
MODULE_OPERATION_LONG_OPTIONS = { "list": ["fields="] }
MODULE_OPERATION_REQUIRED_ARGS = { "list": 1 }

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

