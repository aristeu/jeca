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
from jira import JIRA

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

