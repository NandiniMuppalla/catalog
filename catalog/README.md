#ITEM CATALOG

BY NANDINI MUPPALLA

#Importance of this Project:

In This we use mainly Flask Frame work
In this Item catalog project we do CRUD operartions(CREATE,READ,UPDATE,DELETE)
We perform CRUD operations on Mobiles in this we display mobile categories and mobile versions.
By accessing sql database and OUATH2 provides authentication for crud operations by google account.


##It has three python files mainly I have used in this project.They are:::
mobile.py--->main file to run the project
mobile_dbsetup.py----->sql database is created in this file
mobile_init.py-------->The sample data placed in this file
There are templates it contain html pages 
OUTPUT_SCREENS--->It contains output sample screens

## Skills Required

1. Python
2. HTML
3. CSS
4. OAuth2client
5. DataBaseModels

#Installation steps

1. Install Vagrant & VirtualBox
2. Clone the Udacity Vagrantfile
3. Go to Vagrant directory and either clone this repo or download and place zip here
3. Launch the Vagrant VM (`vagrant up`)
4. Log into Vagrant VM (`vagrant ssh`)
5. Navigate to `cd /vagrant` as instructed in terminal
6. The app imports requests which is not on this vm. Run pip install requests
7. Setup application database `mobile_dbsetup.py`
8. Insert sample data `mobile_init.py`
9. Run application using `mobile.py`
10.Access the application locally using http://localhost:8899

### JSON files

The following are open to the public:

1.mobile Catalog JSON: `'/mobileStore/JSON`
    - Displays the whole cars models catalog. Car Categories and all models.

2.mobile Categories JSON: `/mobileStore/mobile/JSON`
    - Displays all Cars categories
3.All Mobile Editions: `/mobileStore/mob/JSON`
	- Displays all Car Models

4.Car Edition JSON: `'/mobileStore/<path:mobile_name>/mobile/JSON'`
    - Displays Car models for a specific Car category

5.Car Category Edition JSON: `'/mobileStore/<path:mobile_name>/<path:edition_name>/JSON'`
    - Displays a specific Car category Model.
	
## Miscellaneous

This project is inspiration from https://github.com/YVenkatesh7/catalog/blob/master/catalog


