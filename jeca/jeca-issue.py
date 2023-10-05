# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import getopt
import os
import sys
import subprocess
import email
import tempfile
from jira import JIRA
from jeca.alias import alias_translate
from jeca.mbox import issue2mbox, mbox2issue
from jeca.field import get_all_fields, handle_field
from jeca.output import formatted_output

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
    search_filter = [ ]
    saved_search = ""
    save = False
    all_fields = False
    verbose = False
    hide_closed = True
    for option,value in opts:
        if option == '--fields' or option == '-f':
            if value == "all":
                # so, sigh, if you ask too many fields, jira poops its pants
                for i in get_all_fields(jirainst):
                    fields.append(i)
                all_fields = True
                continue
            fields_input = value.split(',')
            for f in fields_input:
                fields.append(alias_translate(config, f))
        elif option == '--project' or option == '-p':
            search_filter.append("project = %s" % value)
        elif option == '--assignee' or option == '-A':
            search_filter.append("assignee = \"%s\"" % value)
        elif option == '--jql':
            jql = value
        elif option == '-s':
            saved_search = value
        elif option == '-S':
            saved_search = value
            save = True
        elif option == '-j':
            search_filter.append("key = \"%s\"" % value)
        elif option == '-V':
            verbose = True
        elif option == '-a':
            hide_closed = False
        else:
            sys.stderr.write("Unknown option: %s\n" % option)
            usage(sys.stderr)
            sys.exit(2)

    if len(fields) == 0:
        # first look if we have a configuration for this
        try:
            for f in config['issue-list']['default_fields'].split(','):
                fields.append(alias_translate(config, f))
        except:
            # pass
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

        if hide_closed == True:
            jql = jql + " and status != closed"

    if len(saved_search) > 0:
        from jeca.config import CONFIG_FILE
        section = "saved_search_%s" % saved_search
        if save == True:
            config_file = open(os.path.expanduser(CONFIG_FILE), 'w')
            if section not in config:
                config.add_section(section)
            config[section]['jql'] = jql
            config[section]['fields'] = ','.join(fields)
            config.write(config_file)
            config_file.close()
            sys.exit(0)

        try:
            jql = config[section]['jql']
            fields = config[section]['fields'].split(',')
        except:
            sys.stderr.write("Unable to find saved search %s in the configuration\n" % saved_search)
            sys.exit(2)


    # FIXME: maxResults should be a config
    try:
        # UGH
        if len(fields) > 20:
            result = jirainst.search_issues(jql_str = jql, maxResults = 500, validate_query = True)
        else:
            result = jirainst.search_issues(jql_str = jql, fields = fields, maxResults = 500, validate_query = True)
    except Exception as ex:
        sys.stderr.write("Error executing search: %s\n" % str(ex))
        sys.exit(2)

    results = []
    for issue in result:
        line = []
        for f in fields:
            tmp = ""
            if verbose is True:
                tmp = tmp + "%s:" % alias_translate(jirainst, f)
            # sigh
            if f == 'key':
                tmp = tmp + issue.key
            else:
                # if the project doesn't have a certain field, it won't return
                # anything. If the field exists but it's not set, it'll return
                # "None"
                try:
                    tmp = tmp + handle_field(jirainst, issue.key, f, issue.raw['fields'][f])
                except:
                    tmp = tmp + "NotDefined"
            line.append(tmp)
        results.append(line)

    formatted_output(results)

    return 0

def op_list_usage(f):
    f.write("jeca %s list [-h|--help]\n\n" % MODULE_NAME)
    f.write("-f,--field <fields>\tspecify the fields shown. 'all' can be used to display all fields but you REALLY don't want that\n")
    f.write("-p,--project <project>\tfilter by project\n")
    f.write("-A,--assignee <user>\tfilter by assignee\n")
    f.write("-s,--saved <name>\tuse saved JQL named <name>\n")
    f.write("-S,--save <name>\tsave JQL as <name> along with --fields. Final filter based on options or --jql will be saved\n")
    f.write("-j <key>\t\tOnly list a specific issue\n")
    f.write("-V\t\tInclude field name in each column with the format \"field:value\"\n")
    f.write("-a\t\tList issues even if they're closed\n")
    f.write("--jql <JQL query>\tspecify the JQL query manually\n")
    f.write("-h|--help\t\tthis message\n")
# list ######

# mbox ######
def op_mbox(config, jirainst, opts, args):
    comment = False
    reply = False
    only_with_aliases = True
    only_official = False
    for option,value in opts:
        if option == '--comment' or option == '-c':
            comment = True
        elif option == "-r":
            reply = True
        elif option == "all_fields":
            only_official = False
            only_with_aliases = False
        elif option == "official":
            # all fields overrides everything
            if only_with_aliases == True:
                only_official = True

    if comment == True:
        # FIXME - someday we can implement support for other email clients, for now it's fixed
        temp = tempfile.NamedTemporaryFile()
        f = open(temp.name, "w")
        issue2mbox(config, f, jirainst, args[0], only_official = only_official, only_with_aliases = only_with_aliases)
        f.close()
        subprocess.run(['mutt', '-f', f.name, '-e', 'set sendmail=\"jeca issue mbox -r\"', '-e', 'set edit_headers=no', '-e', 'set header=no', '-e', 'unset signature', '-e', 'unset record'])
        temp.close()
        return 0
    elif reply == True:
        return mbox2issue(config, sys.stdin, jirainst)

    return issue2mbox(config, sys.stdout, jirainst, args[0], only_official = only_official, only_with_aliases = only_with_aliases)

def op_mbox_usage(f):
    # we don't advertise -r (reply) because it's not supposed to be used
    # we also support -f but it's just compatibility with mutt thinking we're sendmail
    f.write("jeca %s mbox [-c,--comment] <issue>[-h|--help]\n\n" % MODULE_NAME)
    f.write("-c,--comment\tExport issue's comments as mbox and use mutt to comment. Send the email to submit the comment\n")
    f.write("--all_fields\tDisplay all issue's fields in the first email\n")
    f.write("--official\tDisplay only Jira's official issue's fields in the first email\n")
    f.write("-h|--help\t\tthis message\n")
    f.write("\nBy default the first email will have Jira's official issue's fields and custom fields that have aliases\n")

# mbox ######

# set #######
def op_set(config, jirainst, opts, args):
    issue = None
    field = None
    value = None
    for option,v in opts:
        if option == '-j':
            issue = v
        elif option == '-f':
            field = v
        elif option == '-v':
            value = v

    if issue is None or field is None or value is None:
        op_set_usage(sys.stderr)
        sys.exit(1)

    i = jirainst.issue(issue)

    if field == 'status':
        transition_id = None
        for t in jirainst.transitions(i):
            if t['name'] == value:
                transition_id = t['id']
        if transition_id is None:
            sys.stderr.write("Transition to state %s not available\n" % value)
            return 1

        jirainst.transition_issue(issue = i, transition = transition_id)
    else:
        i.update(fields = { field: value })

    return 0

def op_set_usage(f):
    f.write("jeca %s set <-j issue> <-f field> <-v value>[-h|--help]\n\n" % MODULE_NAME)
    f.write("-j issue\t\tissue key/id\n")
    f.write("-f field\t\tfield name or alias to be changed\n")
    f.write("-v value\t\tnew field value\n")
    f.write("-h|--help\t\tthis message\n")
# set #######

# links #####
def op_links(config, jirainst, opts, args):
    fields = [ 'url' ]
    issue = None
    for option,v in opts:
        if option == '-j':
            issue = v
        elif option == '-f':
            fields = v.split(',')

    if issue is None:
        sys.stderr.write("-j must be used\n")
        op_links_usage(sys.stderr)
        return 1

    results = []
    for i in jirainst.remote_links(issue):
        line = []
        for f in fields:
            tmp = ""
            try:
                tmp = tmp + str(i.raw['object'][f])
            except:
                tmp = tmp + "NotDefined"
            line.append(tmp)
        results.append(line)

    formatted_output(results)

    return 0
def op_links_usage(f):
    f.write("jeca %s links <-j issue/key> [-f fields] [-h|--help]\n\n" % MODULE_NAME)
    f.write("-j <issue/key>\t\twhich issue's links should be shown\n")
    f.write("-f <fields>\t\tcomma separated fields to be printed\n")

# links #####

MODULE_NAME = "issue"
MODULE_OPERATIONS = { "list": op_list, "mbox": op_mbox, "set": op_set, "links": op_links }
MODULE_OPERATION_USAGE = { "list": op_list_usage, "mbox": op_mbox_usage, "set": op_set_usage, "links": op_links_usage }
MODULE_OPERATION_SHORT_OPTIONS = { "list": "f:p:A:s:S:j:Va", "mbox": "crf:", "set": "j:f:v:", "links": "j:f:" }
MODULE_OPERATION_LONG_OPTIONS = { "list": ["fields=", "project=", "assignee=", "jql=", "save=", "saved="], "mbox": ["comment","all_fields","official"], "set": [], "links": [] }
MODULE_OPERATION_REQUIRED_ARGS = { "list": 0, "mbox": 1, "set": 0, "links": 0 }

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

