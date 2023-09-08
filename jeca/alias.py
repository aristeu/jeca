# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

def alias_translate(config, field):
    try:
        return config['aliases'][field.lower()]
    except:
        # if no aliases in the config file or there's not an alias
        # to this field
        pass
        return field

def find_alias_for(config, field):
    if 'aliases' in config:
        for i in config['aliases']:
            if config['aliases'][i] == field.lower:
                return i
    return field
