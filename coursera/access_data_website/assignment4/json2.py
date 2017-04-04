import json
import urllib

count=0
total=0
address=raw_input('Enter URL:')
input=urllib.urlopen(address)
info=input.read()
print 'Retrieving', address
print 'Retrieved', len(info), 'characters'
data=json.loads(info)

data=data["comments"]
for item in data:
    total=total+item["count"]
    count=count+1
print 'Count:', count
print 'Sum:', total






