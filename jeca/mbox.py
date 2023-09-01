from dateutil.parser import parse
from datetime import datetime
def issue2mbox(f, jirainst, key):
    for c in jirainst.comments(key):
        updated_datetime = parse(c.updated).ctime()
        f.write("From %s@jeca %s\n" % (str(c.updateAuthor.key), updated_datetime))
        f.write("Message-ID: <%s-%s@jeca>\n" % (c.id, key))
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
