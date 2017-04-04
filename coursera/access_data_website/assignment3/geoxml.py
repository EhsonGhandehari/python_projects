import urllib
import xml.etree.ElementTree as ET

lst=list()
summation=list()
c=0
url = raw_input('Enter location: ')
print 'Retrieving', url
uh = urllib.urlopen(url)
data = uh.read()
print 'Retrieved',len(data),'characters'
tree = ET.fromstring(data)

lst = tree.findall('comments/comment')
    
for count in lst:
    summation.append(int(count.find('count').text))
    c=c+1

print sum(summation)
print c
#    lng = results[0].find('geometry').find('location').find('lng').text
#    location = results[0].find('formatted_address').text

#    print 'lat',lat,'lng',lng
#    print location
