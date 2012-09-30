#!/usr/bin/python

import csv
import httplib
from optparse import OptionParser
import os
import simplejson
import string
import sys
import time

DEBUG = 0
LOCATION_DICT_CHANGED = False

class Location:
  def __init__(self, filename):
    self.cache = {}
    self.filename = filename
    self.changed = False;
    if self.filename:
      try:
        self.cache = simplejson.load(open(self.filename, "r"))
      except:
        pass

  def __del__(self):
    if self.filename:
      cache_file = open(self.filename, "w")
      simplejson.dump(self.cache, cache_file, indent = 2, sort_keys = True)

  def lookup(self, postcode):
    if postcode in self.cache:
      return [self.cache[postcode], True]
    else:
      self.changed = True
      print "Get location for " + postcode
      postcode = string.replace(_postcode," ", "+")
      site = "maps.googleapis.com"
      page = "/maps/api/geocode/json?address=" + postcode + ",+UK&sensor=false"
      url = site + page

      conn = httplib.HTTPConnection(site)
      conn.request("GET", page)
      rl = conn.getresponse()
      data = rl.read()

      datajson = simplejson.loads(data)
      loc = datajson["results"][0]["geometry"]["location"]
      self.cache[postcode] = loc
      return [loc, False]


class Institutions:
  def __init__(self, location, sourcedir):
    self.location = location
    self.sourcedir = sourcedir
    self.cache = {}
    pass

  def __del__(self):
    pass

  def parse(self):
    dirList = os.listdir(self.sourcedir)
    for fname in dirList:
      filepath = self.sourcedir + '/' + fname
      print "Processing", filepath

      csv_in = csv.DictReader(open(filepath, "r"), delimiter = ',')

      for rec in csv_in:
        if "L.POSTCODE" not in rec:
          continue
        if "L.URN" not in rec:
          continue
        if len(rec["L.URN"]) == 0:
          continue

        urn = int(rec["L.URN"])
        self.cache[urn] = {}
        for key in rec:
          self.cache[urn][key] = rec[key]

  def geocode(self):
    count = 0
    for urn in self.cache:

      inst = self.cache[urn];
      postcode = inst["L.POSTCODE"]

      #if option.geocode_only or postcode not in location_dict:
      res = location.lookup(postcode)

      # throttling
      if not res[1]:
        if count % 10 == 0:
          print "timeout"
          time.sleep(2)
        count = count + 1

  def generate_data_begin(self, file):
    file.write('''
  function build_array(map)
  {
  ''')

  def generate_data_marker_begin(self, file):
    file.write('''
    markers =
    [
  ''')

  def get_marker_icon(self, value):
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




  def generate_data_marker_end(self, file):
    file.write('''
    ];
''')


  def generate_data_end(self, file):
    file.write('''
    return markers;

  }
''')

  def generate_glue(self, filename):
    file = open(filename, "w")
    file.write('''

// List of markers
var g_markers = [];

// Singleton for all markers. Only content will be changed
var g_infoWindow = null;

function generateInfoWindowContent(marker)
{
  return marker.title;
}

function initialize()
{
  // Setup map and centre
  var options = {
    center: new google.maps.LatLng(51.5081290, -0.1280050),
    zoom: 12,
    mapTypeId: google.maps.MapTypeId.ROADMAP
  };
  var map = new google.maps.Map(document.getElementById("map_canvas"),
    options);

  // Setup singleton info window for all markers
  g_infoWindow = new google.maps.InfoWindow({ });

  g_markers = build_array(map);

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
}
''')

  def generate_html(self, filename, js1, js2):
    file = open(filename, "w")
    file.write('''
<!DOCTYPE html>
<html>
  <head>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
    <style type="text/css">
      html { height: 100%% }
      body { height: 100%%; margin: 0; padding: 0 }
    </style>

    <script type="text/javascript"
      src="http://maps.googleapis.com/maps/api/js?sensor=false">
    </script>

    <script type="text/javascript"
      src="./%s">
    </script>

    <script type="text/javascript"
      src="./%s">
    </script>

  </head>
  <body onload="initialize()">
    <div id="map_canvas" style="width:100%%; height:100%%"></div>
  </body>
</html>

''' % (js1, js2))


class Schools(Institutions):
  def __init__(self, location, sourcedir, output, ks):
    Institutions.__init__(self, location, sourcedir)
    self.output = output
    self.ks = ks
    if (self.ks == 2):
      self.output_values = ({
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
    else:
      self.output_values = ({
        "L.URN" : "URN",
        "L.RELDENOM" : "Denomination",
        "KS4_11.TOTPUPS"  : "# Pupils",
        "KS4_11.PTAC5EM" : "5+ A*-C GCSEs including English and maths",
        "ABS_11.PERCTOT"   : "Overall absence",
        "CENSUS_11.TSENSAP" : "# Pupils on SEN or School Action Plus",
        "CENSUS_11.PNUMEAL" : "% Pupils with English not as First Language",
        "CENSUS_11.PNUMFSM" : "% Pupils on Free School Meals",
        "SWF_11.RATPUPTEA" : "Pupil:Teacher Ratio",
        "L.NFTYPE" : "School Type",
      })

  def __del__(self):
    Institutions.__del__(self)

  def prepare_output(self):
      # get coordinates from locations map and generate web output
      for urn in self.cache:
        school = self.cache[urn]
        if (self.ks == 2):
          metric = string.replace(school["KS2_11.PTENGMATX"], '%', '')
          if len(metric) > 0 and metric != "SUPP":
            metric = int(metric)
          else:
            0
          school["KS2_11.PTENGMATX"] = metric
        else:
          metric = string.replace(school["KS4_11.PTAC5EM"], '%', '')
          if len(metric) > 0 and metric != "SUPP" and metric != "NE":
            metric = int(metric)
          else:
            0
          school["KS4_11.PTAC5EM"] = metric

        postcode = school["L.POSTCODE"]
        loc = self.location.lookup(postcode)[0]
        school["loc_lat"] = loc["lat"]
        school["loc_lng"] = loc["lng"]
        if (DEBUG):
          print school

  def generate_output(self):
    data_filename = self.output + "_data.js"
    html_filename = self.output + ".html"
    glue_filename = self.output + ".js"

    print "Generating ", data_filename
    self.generate_data(data_filename)

    print "Generating ", glue_filename
    self.generate_glue(glue_filename)

    print "Generating ", html_filename
    self.generate_html(html_filename, data_filename, glue_filename)

  def generate_data(self, filename):
    file = open(filename, "w")
    self.generate_data_begin(file)
    self.generate_data_marker_begin(file)
    for urn in self.cache:
      item = self.cache[urn]
      if (self.ks == 2):
        metric = item["KS2_11.PTENGMATX"]
      else:
        metric = item["KS4_11.PTAC5EM"]
      self.generate_data_marker(file, item, self.get_marker_icon(metric))
    self.generate_data_marker_end(file)

    self.generate_data_end(file)

  def generate_data_marker(self, file, item, icon):
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

    for i in self.output_values:
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
''' % (self.output_values[i], value))

    file.write('''
          ],
        },
''')



# main
parser = OptionParser()
parser.add_option("-d", "--source-dir", action="store", help="Director containing data file")
parser.add_option("-g", "--geocode-only", action="store_true", help="Geocode postcodes and write to file")
parser.add_option("-o", "--output", action="store", help="Filename to store results")
parser.add_option("-l", "--location-map", action="store", help="Cached geo codes")
parser.add_option("-k", "--ks", type="int", action="store", help="Key Stage 2 or 4")

(option, args) = parser.parse_args()

if (DEBUG):
  print "Options: " . option
  print "Arguments: " . args

if option.source_dir == None:
  print "No input dirctory"
  sys.exit(0)
if option.output == None:
  print "No output file given"
  sys.exit(0)
if not option.geocode_only and option.location_map== None:
  print "Neither geocoding option nor input file"
  sys.exit(0)
if option.ks == None:
  print "Key stage number missing"
  sys.exit(0)


location = Location(option.location_map)
schools = Schools(location, option.source_dir, option.output, option.ks)
schools.parse()
schools.geocode()

if not option.geocode_only:
  schools.prepare_output()
  schools.generate_output()


