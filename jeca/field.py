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

def _handle_field(f, field, item):
    try:
        f.write("%s" % item['emailAddress'])
        return
    except:
        pass
    try:
        f.write("%s" % item['name'])
        return
    except:
        pass
    try:
        f.write("%s" % item['value'])
        return
    except:
        pass
    try:
        f.write("%s" % item[field])
        return
    except:
        pass
    f.write("%s" % str(item))

def handle_field(f, field, items):
    if items is None:
        f.write("None")
        return
    if isinstance(items, list):
        first = True
        for item in items:
            if first == False:
                f.write(",")
            first = False
            _handle_field(f, field, item)
    else:
        _handle_field(f, field, items)

