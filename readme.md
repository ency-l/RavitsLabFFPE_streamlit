# Source code for the web-based portal for accessing FFPE blocks inventory at Ravits Lab, UCSD

The portal is developed with streamlit library in python and hosted on streamlit community cloud. 
It fetches data from the google sheet where the block information is stored.
The goal of the page is to make an easy-to-use, intuitive interface that allows filtering for common criteria used in experiment design to quickly view block information.

As of 2025/08/04:
The portal is functional.
TODO:
1. Finish the inventory database. Self-expanatory.
2. Finish implementing filters. Currently the "region" filter is only minimally implemented and only supports the most common categories (Cerv/Thor/Lumb/MC).
3. Potentially integrate data from other spreadsheets (e.g. frozen tissue, main db (once it's hosted online))