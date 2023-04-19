# Search and recommender app

by **team-spirit**<BR>SIADS699 W23<BR>University of Michigan MADS 

## Introduction

Both Airbnb hosts and customers face the daunting task of uncovering how other users truly feel about their Airbnb rental experience. Judging from the qualitative analysis results, customer reviews are influential to customers’ decision-making, and both the sentiment trends and negative reviews are helpful in verifying the rental descriptions and gaining helpful opinions towards the rental. Our interviewees valued negative reviews and even negative sentences in positive reviews up to 50% more than positive reviews.
<BR><BR>
However reading through every review in a large number of listings can be very time consuming. So we decided to see if we could make it easier. Our goal was to use data science to see what kind of content-based recommender system we could make by focusing mostly on the text elements of the rental listings.

## General logic of the recommender system

![app_architecture](https://user-images.githubusercontent.com/101086582/232890030-75571f55-5260-48b6-90d8-86591fab7b80.png)

  
## Web app screen shot

Here is a quick peak at what the app looks like. Be sure to try it live here: [AirBnb Rentals in Seattle](http://3.234.246.45:8501/)  

<img width="588" alt="app_screen_shot" src="https://user-images.githubusercontent.com/101086582/232890575-2a0a9c26-87ca-40b7-a04c-23457e3d9615.png">


## GitHub project file structure

    .
    |____data                               # datasets, survey data, search result rankings
    |____notebooks                          # research jupyter notebooks 
    | |____requirements.txt                 # requirements specific to notebooks
    |____pages                              # web app sub pages
    |____introduction.py                    # web app main page
    |____requirements.txt                   # requirements specific to web app
    |____How to run our Airbnb project.pdf  # explains getting set up and running
    |____README.md                          # this file
    
## Details on getting up and running

Please have a look at the file [How to run our Airbnb project.pdf](https://github.com/clgong/airbnbapp/blob/main/How%20to%20run%20our%20Airbnb%20project.pdf) specific details on:

*    Getting the web app set up and running in these environments
     *    locally
     *    Streamlit
     *    AWS
*    Running our notebooks locally

## A detailed report on our project can be found here:

[SIAD 699 Capstone Project Report - Airbnb Recommender System](https://google.com) 

## Data access statement

We chose three Seattle Airbnb datasets for this project, which was compiled on December 24, 2022, and which can be downloaded from http://insideairbnb.com/get-the-data in CSV format. More detailed information about insideairbnb.com's data use policies can be found at their [data policies page](http://insideairbnb.com/data-policies).


## License

All data sources and python libraries used are open source to the best of our knowledge. If any issues please contact us at clgong at sign umich.edu
