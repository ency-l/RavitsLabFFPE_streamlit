## A web-based portal for accessing FFPE blocks inventory at Ravits Lab, UCSD

The portal is developed with streamlit library in python and hosted on streamlit community cloud. 
It fetches data from the google sheet where the block information is stored.
The goal of the page is to make an easy-to-use, intuitive interface that allows filtering for common criteria used in experiment design to quickly view block information.


### 2025-10-02
----
Finally fixed the streamlit GSheetsConnection API issue. Now the API is properly intergrated per streamlit doc standard. Now it's possible to add data editing to the script.



### 2025-08-10
-----
Functions:
1. Look up information about any block.
2. Criteria mode: Narrow down your searches by filtering with diagnosis (Control/fALS/sALS), or anatomical region(s).
3. Case No. mode: Narrow down your search by filter for specific cases.
4. Filter for active blocks (block that is being used for a specific purpose, and is not in its default location)

To be implemented:
1. Change any information about a block. Please go to the spreadsheet and change it there.
2. See additional information: secondary dx, genetics, pt demographics et c. Please use the MAIN DB spreadsheet. 
