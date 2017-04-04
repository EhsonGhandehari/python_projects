# change the working directory

import os
import re

# make sure to change the directory to local directory

os.chdir('/Users/EhsonMG/Desktop/stuff/transfer/coursera/Python/access_data_website/assignment1')
print(sum(int(i) for i in re.findall('[0-9]+',open('./output.txt').read())))

    


