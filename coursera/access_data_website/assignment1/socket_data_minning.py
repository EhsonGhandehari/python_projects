# Importing the necessary packages

import socket

# Collecting the input website, mines the appropriate domain, and creates a command to scrape the website:


url = raw_input('Enter URl:')
url_host=url.split("//")[1].split("/")[0]
text_file = open("Output1.txt", "w")
command= ('GET '+ url+' HTTP/1.0\n\n')  

# Creates the right socket and connects to the website and reads the data, and writes it into
# output.txt file

mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
mysock.connect((url_host, 80))
mysock.send(command)

while True:
    data = mysock.recv(512)
    if ( len(data) < 1 ) :
        break
    print data;
    text_file.write(data)
    

mysock.close()
text_file.close()

