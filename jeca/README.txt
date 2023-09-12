Don't expect much, this is more of a public backup.

- install python jira library (not atlassian)
- create a ~/.config/jeca/config with:

	[jira]
	url = https://yourjiraserver/
	user = youruser
	token = yourtoken

  you need an API token in Jira: profile, personal access tokens
- link bin/jeca on your PATH:

	$ ln -s $PWD/bin/jeca ~/bin/jeca


Use "jeca <obj> <action> [optons]".

-----------------------

If you use mutt, you can turn the issue into a mbox:

	$ jeca issue mbox FOO-1234 >/tmp/mbox
	$ mutt -f /tmp/mbox

You can also use -c to actually be able to reply to these emails:

	$ jeca issue mbox -c FOO-1234

If you reply to the first (meta) email with lines like:

	summary=new summary

It'll (*maybe*, didn't test much of it and it's likely it'll break in multiple
fields) change in jira. Think of an easier way to change things.

Replying to other emails (comments) will add a new comment with everything.
It's useful to quote part of the comment you're replying to add context to
your reply.

-----------------------

Because everyone has to deal with custom fields and their names are usually
long, full of spaces, use

	$ jeca alias

to maintain a list of aliases for field names so you don't need to remember
"custom_1234567" or "Turbo Sorry Points" and just use "crapoints" or
"tps_ack".

-----------------------

Optional entries in config (likely out of date)

[jira]
default_project = 			# default project to use

[issue-list]
default_jql =				# default JQL expression; overriden if you use options
default_fields = a,b,c,d		# default list of fields to be used by jeca issue list
