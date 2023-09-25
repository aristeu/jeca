# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

from jira import JIRA

def get_all_fields(jirainst):
    result = []
    for f in jirainst.fields():
        result.append(str(f['id']))

    return result

def _handle_field(field, item):
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

def handle_field(field, items):
    if items is None:
        return "None"
    if isinstance(items, list):
        tmp = ""
        first = True
        for item in items:
            if first == False:
                tmp = tmp + ","
            first = False
            tmp = tmp + _handle_field(field, item)
        return tmp
    else:
        return _handle_field(field, items)

