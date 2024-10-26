# inpair

InPost data driven air quality visualisation across Poland

Possible thanks to InPost exposing their [API ShipX](https://dokumentacja-inpost.atlassian.net/wiki/spaces/PL/pages/622754/API+ShipX)

Redesigned to run on Google Cloud Function with HTTP trigger. Generated html page then dropped into Google Cloud Storage bucket with public access and `cache-control: public, max-age=0`

http://www.inpair.pl
