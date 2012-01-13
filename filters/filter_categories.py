"""This input filter will filter out certain blog posts based on the <category>
element.

The following options are available in the .ini file:
filter_categories = ROS, ros, R.O.S., r.o.s.
filter_categories_exceptions = ROS news

"""

import sys
from xml.dom import minidom

entry = sys.stdin.read()
entry_dom = minidom.parseString(entry)
options = dict(zip(sys.argv[1::2],sys.argv[2::2]))

# If a configuration parameter called filter_categories exists then grab it's
# contents and proceed, otherwise allow the entry and exit
filter_categories = options.get('--filter_categories', None)
do_filter = True
if not filter_categories:
    do_filter = False

# figure out if the filter should not be applied
filter_categories_exceptions = options.get('--filter_categories_exceptions', set())
if filter_categories_exceptions:
    filter_categories_exceptions = set([cat.strip() for cat in filter_categories_exceptions.split(',')])

entry_names = entry_dom.getElementsByTagName('planet:name')
for entry_name in entry_names:
    name = " ".join(t.nodeValue for t in entry_name.childNodes if t.nodeType == t.TEXT_NODE)
    if name in filter_categories_exceptions:
        do_filter = False
        break

if not do_filter:
    sys.stdout.write(entry)
    sys.exit(0)

# Break up the comma-separated category list into a list
categories = [cat.strip() for cat in filter_categories.split(',')]

# Collect all the <category> elements from the entry and then see
# if it also happens to be in our required categories list.  If there aren't
# any <category> elements in the entry then skip it
entry_categories = entry_dom.getElementsByTagName('category')

for entry_category in entry_categories:
    if entry_category.attributes['term'].value in categories:
        sys.stdout.write(entry)
        sys.exit(0)

# By default we reject the entry
sys.exit(1)
