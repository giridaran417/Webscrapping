# Webscrapping
This is a webscraping code that scarps the details of PG rooms from https://www.nobroker.in website
1) Install requests and bs4 package using pip.
2) Run the python file.
3) Room details are printed one by one.
4) At last room details are written in the file name ‘roomdetails.pkl’ which is located in the current working directory.
5) Log file named ‘app.log’ also located in the current working directory.
6) Since some areas has large number of PG's it takes little more time to scrab all PG details so by default program fetches first five pages for scrabbing it can be increased by modifying the 'end_page' variable (EX: end_page=30 to fetch 30 pages). 'end_page' variable is in line number 340 or nearer.
7) While running on windows run the program other than C: drive because the python program doesn't have permission to create files in C: drive.  
