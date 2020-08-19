# report-archiver #
Script for cataloging and archiving reports

Some report generator saves its reports to a folder. This script scans all files in this folder, selects report files, and groups them by folder. When the folder is fully assembled, the script will compress it into an archive and move it to a special folder for storing archives.


I set up the launch in my scheduler once a month

### Setup 
In the "configuration.json" file, you must configure the paths to the folder with all reports and the path to the archive folder. Keep in mind that if there is no archive directory along the specified path, the script will create a new one.

All necessary dependencies are specified in "requirements.txt" to install them, use:
    
    pip install -r requirements.txt
or

    pip3 install -r requirements.txt

### Use script 
    python app.py

sorry for my English