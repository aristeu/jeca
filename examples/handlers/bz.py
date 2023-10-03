from jeca.field import new_custom_handler

def bz_handler(field, item):
    return str(item['bugid'])

def init():
    new_custom_handler("customfield_12316840", bz_handler)

