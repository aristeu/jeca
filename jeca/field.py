# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import sys
import os
import glob
import configparser
import re
import time
from jira import JIRA, JIRAError
from jeca.config import FIELD_CACHE

# dictionary of custom field handlers
custom_handlers = {}

def new_custom_handler(field, handler):
    if field in custom_handlers:
        sys.stderr.write("Handler for field %s already exists\n" % field)
        return 1
    custom_handlers[field] = handler
    return 0

def init_all_custom_handlers(config):
    if "misc" not in config or "custom_handlers_path" not in config["misc"]:
        sys.stdout.write("No configuration\n")
        return 0

    handlers = config["misc"]["custom_handlers_path"]
    sys.path.append(handlers)
    for mod in glob.glob("%s/*.py" % handlers):
        module = __import__(os.path.basename(mod).replace(".py", ''))
        module.init()

    return 0

def get_all_fields(jirainst):
    result = []
    try:
        fields = jirainst.fields();
    except JIRAError as http_err:
        if http_err.status_code == 429:
            time.sleep(1)
            fields = jirainst.fields();

    for f in fields:
        result.append(str(f['id']))

    return result

def watchers(jirainst, key, issue):
    results = []
    try:
        watchers = jirainst.watchers(key).watchers;
    except JIRAError as http_err:
        if http_err.status_code == 429:
            time.sleep(1)
            watchers = jirainst.watchers(key).watchers;

    for w in watchers:
        results.append(w.raw['name'])
    return ','.join(results)

def _handle_field(jirainst, key, field, item):
    if field in custom_handlers:
        return custom_handlers[field](field, item)
    if field == 'watchers':
        return watchers(jirainst, key, item)
    try:
        if item.startswith('com.atlassian.greenhopper.service.sprint.Sprint'):
            match = re.search(".*,name=([^,]*).*", item)
            if not match:
                sys.stderr.write("Error parsing sprint string: >%s<\n" % item)
                return "ERROR"
            return match[1]
    except:
        pass
    try:
        return "%s" % item['emailAddress']
    except:
        pass
    try:
        return "%s" % item['name']
    except:
        pass
    try:
        return "%s" % item['value'].replace('\r', '')
    except:
        pass
    try:
        return "%s" % item[field].replace('\r', '')
    except:
        pass
    return str(item).replace('\r', '')

def handle_field(jirainst, key, field, items):
    if items is None:
        return "None"
    if isinstance(items, list):
        tmp = ""
        first = True
        for item in items:
            if first == False:
                tmp = tmp + ","
            first = False
            tmp = tmp + _handle_field(jirainst, key, field, item)
        return tmp
    else:
        return _handle_field(jirainst, key, field, items)

def field_cache(config, jirainst, issue):
    meta = jirainst.editmeta(issue)
    cache = configparser.ConfigParser()
    cache.read(os.path.expanduser(FIELD_CACHE))

    for f_name in meta['fields']:
        f = meta['fields'][f_name]
        fieldid = f['fieldId']
        config_name = "field_%s" % fieldid
        cache[config_name] = {}
        cache[config_name]['required'] = str(f['required'])
        cache[config_name]['type'] = field_type = str(f['schema']['type'])
        cache[config_name]['name'] = f['name']
        if 'items' in f['schema']:
            cache[config_name]['items'] = items = f['schema']['items']
        if 'custom' in f['schema']:
            cache[config_name]['custom'] = f['schema']['custom']
        allowed = []
        if 'allowedValues' in f:
            # FIXME - yep, we could handle properly every field, but
            # this is a lot simpler for now
            if 'name' in f['allowedValues'][0]:
                cache[config_name]['allowed_token'] = token = 'name'
            elif 'value' in f['allowedValues'][0]:
                cache[config_name]['allowed_token'] = token = 'value'
            else:
                raise Exception("Allowed values for %s contains something different than 'name' or 'value' (%s)" % (f_name, str(f['allowedValues'][0])))
            for a in f['allowedValues']:
                allowed.append(a[token])
            cache[config_name]['allowed'] = ','.join(allowed)
    # le sigh
    resolutions = []
    for i in jirainst.resolutions():
        resolutions.append(str(i))

    config_name = "field_resolution"
    cache[config_name] = {}
    cache[config_name]['required'] = "False"
    cache[config_name]['type'] = "option"
    cache[config_name]['name'] = "Resolution"
    cache[config_name]['allowed'] = ','.join(resolutions)

    f = open(os.path.expanduser(FIELD_CACHE), 'w')
    cache.write(f)

def field_cache_get(config, jirainst, name):
    cache = configparser.ConfigParser()
    cache.read(os.path.expanduser(FIELD_CACHE))
    field_name = "field_%s" % name

    if field_name not in cache:
        return None

    rc = cache[field_name]
    return rc

def field_cache_get_allowed(config, jirainst, name):
    cache = field_cache_get(config, jirainst, name)
    if cache is None:
        return None

    if 'allowed' not in cache:
        return []

    return cache['allowed']

def get_field_token(cache):
    # sigh
    if 'custom' in cache and cache['custom'] == "com.pyxis.greenhopper.jira:gh-sprint":
        return 'direct'

    # if the field has allowed values, we can quickly determine if it's 'value' or 'name'
    if 'allowed_token' in cache:
        return cache['allowed_token']

    if cache['type'] == 'option':
        return 'value'

    if cache['type'] == 'date' or cache['type'] == 'number' or cache['type'] == 'string':
        return 'direct'

    return 'name'

def handle_sprint(config, jirainst, issue, cache, value):
    bcount = 0
    max_count = 500
    while True:
        l =jirainst.boards(projectKeyOrID=config['jira']['default_project'], maxResults = max_count, startAt=bcount)
        for board in l:
            if board.type != 'scrum':
                continue
            scount = 0
            while True:
                s = jirainst.sprints(board_id = board.id, maxResults = max_count, startAt=scount)
                for sprint in s:
                    if sprint.name == value:
                        return sprint.id
                if len(s) < max_count:
                    break
                scount = scount + max_count

        if len(l) < max_count:
            break
        bcount = bcount + max_count
    return None

def convert_field(config, jirainst, issue, cache, value):
    if 'custom' in cache:
        if cache['custom'] == "com.atlassian.jira.plugin.system.customfieldtypes:float":
            return float(value)
        if cache['custom'] == "com.pyxis.greenhopper.jira:gh-sprint":
            if value.isdigit():
                return int(value)
            ret = handle_sprint(config, jirainst, issue, cache, value)
            if ret is None:
                sys.stderr.write("Unable to find sprint '%s'\n" % value)
                sys.exit(1)
            return ret
    if cache['type'] == 'number':
        return int(value)

    return value

def field_handle_set(config, jirainst, issue, name, value):
    cache = field_cache_get(config, jirainst, name)
    if cache is None:
        sys.stderr.write("Unable to find '%s' in cache, please make sure the field exists or run jeca field cache\n" % name)
        return 1
    token = get_field_token(cache)
    value = convert_field(config, jirainst, issue, cache, value)
    final_value = {}
    if token == 'direct':
        final_value[name] = value
    elif cache['type'] == 'array':
        output = []
        value = value.split(',')

        for item in value:
            if len(item.replace(' ', '')) == 0:
                continue
            data = {}
            data[token] = item
            output.append(data)
        final_value[name] = output
    else:
        final_value = {}
        final_value[name] = {token: value}

    try:
        issue.update(fields = final_value)
    except JIRAError as http_err:
        if http_err.status_code == 429:
            time.sleep(1)
            issue.update(fields = final_value)

    return 0

def field_translate_jql(config, jirainst, jql):
    try:
        cache = configparser.ConfigParser()
        cache.read(os.path.expanduser(FIELD_CACHE))
    except:
        sys.stderr.write("Unable to open field cache. Please run jeca field cache\n")
        sys.exit(1)

    # first process aliases
    jql_split = jql.replace('=', ' ').split()
    for a in config['aliases']:
        if a in jql_split:
            jql = jql.replace(a, config['aliases'][a])

    # then process everything once you have the fields' real names
    jql_split = jql.replace('=', ' ').split()
    for field_name in cache:
        n = field_name.replace('field_', '', 1)
        if n in jql_split:
            # need the quotes
            jql = jql.replace(n, "'%s'" % cache[field_name]['name'])

    return jql
