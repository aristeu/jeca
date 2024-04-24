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
from jira import JIRA
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
    for f in jirainst.fields():
        result.append(str(f['id']))

    return result

def watchers(jirainst, key, issue):
    results = []
    for w in jirainst.watchers(key).watchers:
        results.append(w.raw['name'])
    return ','.join(results)

def _handle_field(jirainst, key, field, item):
    if field in custom_handlers:
        return custom_handlers[field](field, item)
    if field == 'watchers':
        return watchers(jirainst, key, item)
    try:
        return "%s" % item['emailAddress']
    except:
        pass
    try:
        return "%s" % item['name']
    except:
        pass
    try:
        return "%s" % item['value']
    except:
        pass
    try:
        return "%s" % item[field]
    except:
        pass
    return str(item)

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
    # if the field has allowed values, we can quickly determine if it's 'value' or 'name
    if 'allowed_token' in cache:
        return cache['allowed_token']

    if cache['type'] == 'option':
        return 'value'

    if cache['type'] == 'date':
        return 'direct'

    return 'name'

def field_handle_set(config, jirainst, issue, name, value):
    cache = field_cache_get(config, jirainst, name)
    if cache is None:
        sys.stderr.write("Unable to find '%s' in cache, please make sure the field exists or run jeca field cache\n" % name)
        return 1
    token = get_field_token(cache)
    final_value = {}
    if cache['type'] == 'array':
        output = []
        value = value.split(',')

        for item in value:
            data = {}
            data[token] = item
            output.append(data)
        final_value[name] = output
    elif token == 'direct':
        final_value[name] = value
    else:
        final_value = {}
        final_value[name] = {token: value}

    issue.update(fields = final_value)

    return 0
