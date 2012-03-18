#!/usr/bin/python

import csv
import httplib
from optparse import OptionParser
import os
import simplejson
import string
import sys
import time


def geocode(_postcode):
  postcode = string.replace(_postcode," ", "+")
  site = "maps.googleapis.com"
  page = "/maps/api/geocode/json?address=" + postcode + ",+UK&sensor=false"
  url = site + page
  #print page

  conn = httplib.HTTPConnection(site)
  conn.request("GET", page)
  rl = conn.getresponse()
  #print rl.status, rl.reason
  data = rl.read()
  #print data

  datajson = simplejson.loads(data)
  loc = datajson["results"][0]["geometry"]["location"]
  return loc

def resolve_nftype(type, urn ):
  if type == "20":
    return "Sponsored Academy"
  if type == "21":
    return "Community School"
  elif type == "22":
    return "Voluntary Aided School"
  elif type == "23":
    return "Voluntary Controlled School"
  elif type == "24":
    return "Foundation School"
  elif type == "25":
    return "City Technology College"
  elif type == "26":
    return "Community Special School"
  elif type == "27":
    return "Foundation Special School"
  elif type == "28":
    return "Non-Maintained Special School"
  elif type == "30":
    return "Independent School"
  elif type == "31":
    return "Further Education Sector Institution"
  elif type == "35":
    return "Sixth Form Centre"
  elif type == "48":
    return "Other Independent Special School"
  elif type == "51":
    return "Academy"
  elif type == "52":
    return "Free School"
  elif type == "311":
    return "Agriculture and Horticulture College"
  elif type == "313":
    return "General Further Education College"
  elif type == "315":
    return "Sixth Form College"
  elif type == "318":
    return "Specialist Designated College"
  elif type == "319":
    return "Tertiary College"
  else:
    print urn
    print type
    return type

def resolve_reldenom(type, urn ):
  if type == "0":
    return "Does not apply"
  if type == "2":
    return "Church of England"
  if type == "3":
    return "Roman Catholic"
  if type == "4":
    return "Methodist"
  if type == "5":
    return "Jewish"
  if type == "6":
    return "None"
  if type == "7":
    return "Muslim"
  if type == "8":
    return "Seventh Day Adventist"
  if type == "15":
    return "Christian"
  if type == "21":
    return "Sikh"
  if type == "22":
    return "Greek Orthodox"
  if type == "23":
    return "Unitarian"
  if type == "25":
    return "Hindu"
  if type == "28":
    return "Inter- / non- denominational"
  if type == "29":
    return "Multi-faith"
  if type == "99":
    return "Unknown"
  else:
    print urn
    print type
    return type

def generate_code_begin(file):
  file.write('''

// List of markers
var g_markers = [];

// Singleton for all markers. Only content will be changed
var g_infoWindow = null;

function generateInfoWindowContent(marker)
{
  return marker.title;
}

function initialize() {
  // Setup map and centre
  var options = {
    center: new google.maps.LatLng(51.5081290, -0.1280050),
    zoom: 12,
    mapTypeId: google.maps.MapTypeId.ROADMAP
  };
  var map = new google.maps.Map(document.getElementById("map_canvas"),
    options);


  // Setup singleton info window for all markers
  var g_infoWindow = new google.maps.InfoWindow({ });

''')

def generate_code_marker_begin(file):
  file.write('''
  g_markers =
  [
''')

def get_marker_icon(value):
  image = ""
  if value == 0:
    image = "na.png"
  elif value >= 95:
    image = "1.png"
  elif value >= 90:
    image = "2.png"
  elif value >= 85:
    image = "3.png"
  elif value >= 80:
    image = "4.png"
  elif value >= 75:
    image = "5.png"
  elif value >= 70:
    image = "6.png"
  else:
    image = "50.png"

  return "img/" + image


def generate_code_marker(file, item, icon):
  file.write('''
      {
        c :
        {
          position: new google.maps.LatLng(%f, %f),
          map: map,
          title: "%s",
          icon: "%s"
        },
        d :
        [
''' % (item["loc_lat"], item["loc_lng"], item["L.SCHNAME"], icon))

  for i in output_values:
    value = ""
    if i in item:
      value = item[i]
    else:
      value = "No data"
    file.write('''
          {
            name : "%s",
            value : "%s"
          },
''' % (output_values[i], value))

  file.write('''
        ],
      },
''')


def generate_code_marker_end(file):
  file.write('''
  ];

  for (i in g_markers)
  {
    var item = g_markers[i];
    var marker = new google.maps.Marker(item.c);
    marker.user_data = item.d;

    google.maps.event.addListener(marker, 'click', function() {
      var content = "<div><h2>" + this.title + "</h2><br>";
      content += "<table border='1'>"
      var data = this.user_data;
      for (i in data)
      {
        item = data[i]
        if (item["name"] == "URN")
          content += "<tr><td>Link</td><td><a href='http://www.education.gov.uk/cgi-bin/schools/performance/school.pl?urn=" + item["value"] + "'>" + item["value"] + "</a></td></tr>"
	else
          content += "<tr><td>" + item["name"] + "</td><td>" + item["value"] + "</td></tr>";
      }
      content += "</table>";
      g_infoWindow.setContent(content);
      //g_infoWindow.setContent(this.title);
      g_infoWindow.open(map, this);
    });
  }
''')


def generate_code_end(file):
  file.write('''
}
''')

def generate_code(filename):
  file = open(filename, "w")
  generate_code_begin(file)
  generate_code_marker_begin(file)
  for urn in school_dict:
    item = school_dict[urn]
    if "KS2_11.PTENGMATX" not in item:
      continue
#    generate_code_marker(file, item["lat"], item["lng"], item["SCHNAME"],
#      get_marker_icon(item["PTENGMATX"]))
    generate_code_marker(file, item, get_marker_icon(item["KS2_11.PTENGMATX"]))
  generate_code_marker_end(file)

  generate_code_end(file)




parser = OptionParser()
parser.add_option("-d", "--source-dir", action="store", help="Director containing data file")
parser.add_option("-g", "--geocode-only", action="store_true", help="Geocode postcodes and write to file")
parser.add_option("-o", "--output", action="store", help="File to store results")
parser.add_option("-l", "--location-map", action="store", help="Cached geo codes")

(option, args) = parser.parse_args()

#print option
#print args

if option.source_dir == None:
  print "No input dirctory"
  sys.exit(0)
if option.output == None:
  print "No output file given"
  sys.exit(0)
if not option.geocode_only and option.location_map== None:
  print "Neither geocoding option nor input file"
  sys.exit(0)



location_dict = {}
if option.location_map != None:
#  location_file = open(option.location_map, "r")
  location_dict = simplejson.load(open(option.location_map, "r"))

school_dict = {}

output_values = ({
  "L.URN" : "URN",
  "L.RELDENOM" : "Denomination",
  "KS2_11.TOTPUPS"  : "# Pupils",
  "KS2_11.PTENGMATX" : "Level 4 in Math and English",
  "ABS_11.PERCTOT"   : "Overall absence",
  "CENSUS_11.TSENSAP" : "# Pupils on SEN or School Action Plus",
  "CENSUS_11.PNUMEAL" : "% Pupils with English not as First Language",
  "CENSUS_11.PNUMFSM" : "% Pupils on Free School Meals",
  "SWF_11.RATPUPTEA" : "Pupil:Teacher Ratio",
  "L.NFTYPE" : "School Type",
})

dir = option.source_dir
dirList = os.listdir(dir)
for fname in dirList:
  filepath = dir + '/' + fname
  print "Processing", filepath

  csv_in = csv.DictReader(open(filepath, "r"), delimiter = ',')

  for rec in csv_in:
    if len(rec["L.URN"]) == 0:
      continue
    if "L.POSTCODE" not in rec:
      continue

    urn = int(rec["L.URN"])
    school_dict[urn] = {}
    for key in rec:
      school_dict[urn][key] = rec[key]


count = 0
for urn in school_dict:

    school = school_dict[urn];

    postcode = school["L.POSTCODE"]

    if option.geocode_only or postcode not in location_dict:
      print "Get location for " + postcode
      # throttling
      if count % 10 == 0:
        print "timeout"
        time.sleep(2)
      count = count + 1
      # perform lookup and store
#      print postcode
      location = geocode(postcode)
#      print location
      location_dict[postcode] = location
    if not option.geocode_only:
      # get coordinates from locations map and generate web output
      PTENGMATX = string.replace(school["KS2_11.PTENGMATX"], '%', '')
      PTENGMATX = int(PTENGMATX) if len(PTENGMATX) > 0 and PTENGMATX != "SUPP" else 0
      school["KS2_11.PTENGMATX"] = PTENGMATX
      school["L.NFTYPE"] = resolve_nftype(school["L.NFTYPE"], urn)
      school["L.RELDENOM"] = resolve_reldenom(school["L.RELDENOM"], urn)
      school["loc_lat"] = location_dict[postcode]["lat"]
      school["loc_lng"] = location_dict[postcode]["lng"]
      #print school


# save location maps to file
location_file = open(option.location_map, "w")
simplejson.dump(location_dict, location_file, indent = 2)

if not option.geocode_only:
  # Generate Javascript with data
  generate_code(option.output);

