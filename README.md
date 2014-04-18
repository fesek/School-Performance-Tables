**Latest stable version is 6d30b79d97 in conjunction with 2012 data set. I am currently refactoring the logic to separate out code and data.**

Script parsing school performance data available from the UK's Department of Education's website and mapping the results using Google Maps.

After geocoding the school's postcode, a marker is placed on the map representing the school's performance in English and Math. Additional key values are displayed in a pop up.

The entire process is offline. Geocoding can be done in a separate step and cached in a local file for future reuse without abusing Google's API limitations. Downloaded CSV files are read from a dedicated directory. The result is a Javascript file containing the data, another Javascript file with basic code (static) to hook up with Google Maps and a (semi-static) HTML file including the former.

Notes:
 * A Google API key may need to be added to the html file.
 * Fetch files from the "Download all" columns of the page below. The script works with KS2 and KS4 files.

Sample invocation (with KS2 data files):
  ./lookup.py  -d data/ -k 2 -o london_ks2 -l sample/location_map 


Files:
* lookup.py
  *  Actual script
* london_ks2.html
  * simple webpage including generated JS
* london_ks2_data.js
  * JSON objects representing school data
* london_ks2.js
  * Basic Javscript code instantiating the data and Google Maps
* location_map
  * pre-built cache of London's schools' postcodes
  

Links:
* Data files
  * http://www.education.gov.uk/schools/performance/download_data.html
* Homepage Department of Education - School Performance
  * http://www.education.gov.uk/schools/performance/
