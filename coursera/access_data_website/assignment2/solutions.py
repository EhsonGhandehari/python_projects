# Note - this code must run in Python 2.x and you must download
# http://www.pythonlearn.com/code/BeautifulSoup.py
# Into the same folder as this program

import urllib
import re
from BeautifulSoup import *
lst=list()
url = raw_input('Enter URl:')
position=int(raw_input('Enter Position:'))
counts=int(raw_input('Enter Counts:'))

html = urllib.urlopen(url).read()
soup = BeautifulSoup(html)

# Retrieve all of the anchor tags
tags = soup('a')

for i in range(counts):
    for tag in tags:
        lst.append(tag.get('href', None))
    url=lst[position-1]
    print "Retrieving: ",url
    html = urllib.urlopen(url).read()
    soup = BeautifulSoup(html)
    tags=soup('a')
    lst=[]

print(re.findall('_([a-zA-Z]*).htm',url))[0]
