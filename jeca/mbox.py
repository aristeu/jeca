from email import message_from_file
from email import policy
import re
import sys

from dateutil.parser import parse
from datetime import datetime

from jeca.alias import find_alias_for
from jeca.field import handle_field

# issue.id
# issue.self (url)
# issue.key
# for i in issue.raw:
#    print(str(issue.raw[i]))
#    for i in issue.raw['fields']:
#        print("%s = %s" % (i, issue.raw['fields'][i]))

reject_field_list = ['comment', 'issuelinks', 'description', 'attachment', 'watches']
# issue2mbox: writes a mbox using an issue. Issue's properties are available
#             in the thread's first email. Comments are separate emails
#             replying to the first email
# only_with_aliases: only output custom fields that have aliases assigned to them
# only_official: only output official jira fields, ignoring all custom ones
def issue2mbox(config, f, jirainst, key, only_with_aliases = False, only_official = False):
    issue = jirainst.issue(key)
    updated_datetime = parse(issue.fields.updated).ctime()
    fields = jirainst.fields()
    field_db = {}
    custom_fields = []

    # caching so we don't fetch one field at the time
    for field in fields:
        field_db[field['id']] = field['name']
        if field['custom'] == True:
            custom_fields.append(field['id'])

    # first the "meta" email containing everything the issue has
    f.write("From %s@jeca %s\n" % (str(issue.fields.creator.key), updated_datetime))
    f.write("Message-ID: <0-%s@jeca>\n" % key)
    f.write("Date: %s\n" % updated_datetime)
    f.write("From: %s <%s@jeca>\n" % (issue.fields.creator.displayName, issue.fields.creator.key))
    f.write("To: you <jeca@jeca>\n")
    f.write("Subject: %s\n\n" % issue.key)

    f.write("%s %s\n" % (issue.key, issue.self))
    f.write("Created by %s <%s> on %s\n\n" % (issue.fields.creator.displayName, issue.fields.creator.emailAddress, updated_datetime))

    f.write("Below are this issue's fields and their values. You can reply to this email with a new value in the format below to change:\n\tfield=new value\n\n")

    for field in issue.raw['fields']:
        if field in reject_field_list:
            continue
        if only_with_aliases == True and field in custom_fields and field == find_alias_for(config, field):
            continue
        if only_official == True and field in custom_fields:
            continue

        f.write("# %s (%s)\n" % (field_db[field], field))
        # fields can point to various objects, so attempt to guess what the value is
        f.write("%s=" % find_alias_for(config, field))
        f.write(handle_field(jirainst, issue.key, field, issue.raw['fields'][field]))
        f.write("\n\n")

    # description as the first reply
    created_time = parse(issue.fields.created).ctime()
    f.write("From %s@jeca %s\n" % (str(issue.fields.creator.key), created_time))
    f.write("Message-ID: <1-%s@jeca>\n" % key)
    f.write("In-Reply-To: <0-%s@jeca>\n" % key)
    f.write("Date: %s\n" % created_time)
    f.write("From: %s <%s@jeca>\n" % (issue.fields.creator.displayName, issue.fields.creator.key))
    f.write("To: you <jeca@jeca>\n")
    f.write("Subject: Description\n\n")
    f.write(issue.raw['fields']['description'])
    f.write("\n\n")

    # now comments as emails replying to the "meta" email
    for c in jirainst.comments(key):
        updated_datetime = parse(c.updated).ctime()
        f.write("From %s@jeca %s\n" % (str(c.updateAuthor.key), updated_datetime))
        f.write("Message-ID: <%s-%s@jeca>\n" % (c.id, key))
        f.write("In-Reply-To: <0-%s@jeca>\n" % key)
        f.write("Date: %s\n" % updated_datetime)
        f.write("From: %s <%s@jeca>\n" % (c.updateAuthor.displayName, c.updateAuthor.key))
        f.write("To: you <jeca@jeca>\n")
        f.write("Subject: ")
        try:
            if str(c.visibility.type) == "group":
                f.write("[PRIVATE] ")
        except:
            pass
        f.write("Comment from %s\n\n" % c.updateAuthor.displayName)
        f.write("%s\n\n" % str(c.body))
    return 0

def handle_field_change(config, jirainst, key, body):
    lines = body.split('\n')

    out = {}

    for line in lines:
        if line.startswith("> "):
            continue
        if len(line.replace(' ', '')) == 0:
            continue
        if line.startswith("On "):
            continue
        line = re.sub(r'[\s]*=[\s]*', '=', line)
        l = line.split('=')
        index = l[0]
        try:
            value = l[1].split(',')
        except:
            sys.stdout.write("Ignored line: [%s]\n" % line)
            pass
            continue

        if len(value) > 1:
            out[index] = value
        else:
            out[index] = l[1]
    issue = jirainst.issue(key)
    issue.update(fields = out)


def mbox2issue(config, f, jirainst):
    e = message_from_file(f, policy=policy.default)

    irt = e.get("In-Reply-To")
    if irt is None:
        sys.stderr.write("In-Reply-To not found in headers. Check your email client\n")
        return 1

    # The In-Reply-To contains the comment id and the issue key
    email_re = re.compile('.*<([^>\-@]+)-([^>@]+)[^>]+>.*', re.S)
    match = email_re.match(irt)
    if match is None:
        sys.stderr.write("Invalid In-Reply-To format: %s\n" % irt)
        return 1
    comment_id = match.group(1)
    key = match.group(2)

    # Now find out if it's the first email of the thread, which contains issue
    # fields that can be edited. Otherwise, we'll handle it as just a comment to
    # be added
    if comment_id == "0":
        handle_field_change(config, jirainst, key, e.get_payload())
    else:
        private_type = None

        if comment_id != "1":
            comment = jirainst.comment(issue = key, comment = comment_id)
            try:
                private_type = comment.visibility.type
                private_value = comment.visibility.value
            except:
                private_value = None

        if private_type is not None:
            jirainst.add_comment(key, e.get_payload(), visibility = { "type": private_type, "value": private_value })
        else:
            jirainst.add_comment(key, e.get_payload())

    return 0
