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
