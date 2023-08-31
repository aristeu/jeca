# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import getopt
import sys
import os
from jira import JIRA

# list ######
def op_list(config, jirainst, opts, args):

    if "aliases" not in config:
        return 0

    for a in config['aliases']:
        sys.stdout.write("%s\t%s\n" % (a, config['aliases'][a]))

    return 0

def op_list_usage(f):
    f.write("jeca %s list [-h|--help]\n\n" % MODULE_NAME)
    f.write("-h|--help\t\tthis message\n")
# list ######

# new #######
def op_new(config, jirainst, opts, args):
    # FIXME this breaks when specifying the config file as global command option
    from jeca.config import CONFIG_FILE

    if "aliases" not in config:
        config['aliases'] = {}
    config['aliases'][args[0]] = args[1]
    config_file = open(os.path.expanduser(CONFIG_FILE), 'w')
    config.write(config_file)

    return 0

def op_new_usage(f):
    f.write("jeca %s new <alias> <field> [-h|--help]\n\n" % MODULE_NAME)
    f.write("<alias> is case insensitive\n")
    f.write("-h|--help\t\tthis message\n")
# new #######

# rm ########
def op_rm(config, jirainst, opts, args):
    from jeca.config import CONFIG_FILE

    if "aliases" not in config or args[0] not in config['aliases']:
        sys.stderr.write("Alias %s not found in the config file\n" % args[0])
        return 1

    config['aliases'].pop(args[0])
    config_file = open(os.path.expanduser(CONFIG_FILE), 'w')
    config.write(config_file)

    return 0

def op_rm_usage(f):
    f.write("jeca %s rm <alias> [-h|--help]\n\n" % MODULE_NAME)
    f.write("-h|--help\t\tthis message\n")
# rm ########

MODULE_NAME = "alias"
MODULE_OPERATIONS = { "list": op_list, "new": op_new, "rm": op_rm }
MODULE_OPERATION_USAGE = { "list": op_list_usage, "new": op_new_usage, "rm": op_rm_usage }
MODULE_OPERATION_SHORT_OPTIONS = { "list": '', "new": '', "rm": '' }
MODULE_OPERATION_LONG_OPTIONS = { "list": [], "new": [], "rm": [] }
MODULE_OPERATION_REQUIRED_ARGS = { "list": 0, "new": 2, "rm": 1 }

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

