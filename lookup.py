#!/usr/bin/python

import csv
import httplib
from optparse import OptionParser
import os
import simplejson
import string
import sys
import time
import re

DEBUG = 0
LOCATION_DICT_CHANGED = False

class Locations:
  def __init__(self, filename):
    self.filename = filename
    self.changed = False;
    self.throttle_count = 0

    self.cache = {}
    if self.filename:
      try:
        self.cache = simplejson.load(open(self.filename, "r"))
      except:
        pass

  def __del__(self):
    if self.changed and self.filename:
      cache_file = open(self.filename, "w")
      simplejson.dump(self.cache, cache_file, indent = 2, sort_keys = True)

  def lookup(self, postcode):
    if postcode in self.cache:
      return self.cache[postcode]
    else:
      print "Postcode ", postcode, " not in cache"
      # throttling
      self.throttle_count = self.throttle_count + 1
      if self.throttle_count % 10 == 0:
        print "timeout"
        time.sleep(2)

      # Request location
      self.changed = True
      print "Get location for " + postcode
      site = "maps.googleapis.com"
      page = "/maps/api/geocode/json?address=" + postcode.replace(" ", "+") + ",+UK&sensor=false"
      url = site + page

      conn = httplib.HTTPConnection(site)
      conn.request("GET", page)
      rl = conn.getresponse()
      data = rl.read()

      datajson = simplejson.loads(data)
      loc = datajson["results"][0]["geometry"]["location"]
      self.cache[postcode] = loc

      return loc


class Institutions:
  def __init__(self, locations, sourcedir):
    self.locations = locations
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
        # discard invalid entries
        if not self.valid(rec):
          continue

        if self.filter(rec):
          continue

        # create and populate entry
        inst = {}
        for key in rec:
          inst[key] = rec[key]

        urn = self.getUrn(inst)

        # add location
        postcode = self.getPostcode(inst)
        loc = self.locations.lookup(postcode)
        inst["loc_lat"] = loc["lat"]
        inst["loc_lng"] = loc["lng"]

        # set metric (used for icons later)
        inst["__name__"] = self.get_name(inst)
        inst["__metric__"] = self.get_metric(inst)
        inst["__icon__"] = self.get_icon(inst)

        # add to cache
        if (DEBUG):
          print inst
        self.cache[urn] = inst


class Schools(Institutions):
  def __init__(self, locations, sourcedir, ks):
    Institutions.__init__(self, locations, sourcedir)
    self.link = "http://www.education.gov.uk/cgi-bin/schools/performance/school.pl?urn="
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

  def valid(self, rec):
    if "L.POSTCODE" not in rec:
      return False
    if "L.URN" not in rec:
      return False
    if len(rec["L.URN"]) == 0:
      return False
    return True

  def filter(self, rec):
    return False

  def getUrn(self, inst):
    return int(inst["L.URN"])

  def getPostcode(self, inst):
    return inst["L.POSTCODE"]

  def get_name(self, inst):
    return inst["L.SCHNAME"]

  def get_metric(self, inst):
    if (self.ks == 2):
      metric = string.replace(inst["KS2_11.PTENGMATX"], '%', '')
      if len(metric) > 0 and metric != "SUPP":
        return int(metric)
      else:
        return 0
    else:
      metric = string.replace(inst["KS4_11.PTAC5EM"], '%', '')
      if len(metric) > 0 and metric != "SUPP" and metric != "NE":
        return int(metric)
      else:
        return 0

  def get_icon(self, inst):
    value = inst["__metric__"]
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

  def write(self, output):
    output.generate(self.cache, self.output_values, self.link)

class Nurseries(Institutions):
  def __init__(self, locations, sourcedir, ks):
    Institutions.__init__(self, locations, sourcedir)
    self.link = "http://www.ofsted.gov.uk/inspection-reports/find-inspection-report/provider/CARE/"
    self.ks = ks
    self.output_values = ({
      "Provider URN" : "URN",
      "Provider Status" : "Status",
      "Individual Register Combinations" : "Register",
      "Provider Name" : "Name",
      "Provider Address 1" : "Address 1",
      "Provider Address 2" : "Address 2",
      "Provider Address 3" : "Address 3",
      "Provider Postcode1" : "Postcode",
      "How well does the setting meet the needs of children in the Early Years Foundation Stage?" : "Setting",
      "The capacity of the provision to maintain continuous improvement." : "continuous improvement",
      "The effectiveness of leadership and management of the Early Years Foundation Stage" : "Leadership and management",
      "The quality of provision in the Early Years Foundation Stage" : "Quality",
      "Outcomes for children in the Early Years Foundation Stage" : "Outcomes",
      "Quality of provision (CCR)" : "Compulsory requirements",
      "Quality of provision (VCR)" : "Voluntary requirements",
    })

  def __del__(self):
    Institutions.__del__(self)

  def valid(self, rec):
    if len(rec["Provider URN"]) == 0:
      #print "skip " + rec["Provider URN"]
      return False
    if rec["Provider Postcode1"] == "RETN":
      #print "skip " + rec["Provider Postcode1"]
      return False
    if rec["Provider Postcode1"] == "Redacted":
      #print "skip " + rec["Provider Postcode1"]
      return False
    return True

  def filter(self, rec):
    postcode = self.getPostcode(rec)

    # Limit to London
    expression = "(EC|WC)|((NW|N|E|SE|SW|W)[\d]+) "
    found = re.match(expression, postcode) != None
    return not found

  def getUrn(self, inst):
    return inst["Provider URN"]

  def getPostcode(self, inst):
    return inst["Provider Postcode1"]

  def get_name(self, inst):
    return inst["Provider Name"]

  def get_metric(self, inst):
    return inst["How well does the setting meet the needs of children in the Early Years Foundation Stage?"]

  def get_icon(self, inst):
    value = inst["__metric__"]
    image = ""
    if value == "1":
      image = "1.png"
    elif value == "2":
      image = "2.png"
    elif value == "3":
      image = "3.png"
    elif value == "4":
      image = "4.png"
    elif value == "5":
      image = "5.png"
    else:
      image = "na.png"

    return "img/" + image

  def write(self, output):
    output.generate(self.cache, self.output_values, self.link)

class Output:
  def __init__(self, output):
    self.data_filename = output + "_data.js"
    self.html_filename = output + ".html"
    self.glue_filename = output + ".js"

  def __del__(self):
    pass

  def generate(self, cache, output_values, link):
    self.cache = cache
    self.output_values = output_values
    self.link = link

    self.generate_data(cache)
    self.generate_glue()
    self.generate_html()

  def escape (self, value):
    return value.replace('"', '\\"')

  def generate_data(self, cache):
    print "Generating data file " + self.data_filename
    file = open(self.data_filename, "w")
    self.generate_data_begin(file)
    self.generate_data_marker_begin(file)

    count = 0
    for urn in cache:
      count = count + 1
      item = cache[urn]
      self.generate_data_marker(file, item, item["__icon__"])
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
''' % (item["loc_lat"], item["loc_lng"], self.escape(item["__name__"]), icon))

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
''' % (self.output_values[i], self.escape(value)))

    file.write('''
          ],
        },
''')


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

  def generate_data_marker_end(self, file):
    file.write('''
    ];
''')


  def generate_data_end(self, file):
    file.write('''
    return markers;

  }
''')

  def generate_glue(self):
    print "Generating data file " + self.glue_filename
    file = open(self.glue_filename, "w")
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
          content += "<tr><td>Link</td><td><a href='%s" + item["value"] + "'>" + item["value"] + "</a></td></tr>"
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
''' % (self.link))

  def generate_html(self):
    print "Generating data file " + self.html_filename
    file = open(self.html_filename, "w")
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

''' % (self.data_filename, self.glue_filename))




# main
parser = OptionParser()
parser.add_option("-d", "--source-dir", action="store", help="Director containing data file")
parser.add_option("-o", "--output", action="store", help="Filename to store results")
parser.add_option("-l", "--location-map", action="store", help="Cached geo codes")
parser.add_option("-t", "--type", action="store", help="[s]chool or [n]ursery")
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
if option.type == "s" and option.ks == None:
  print "Key stage number missing"
  sys.exit(0)


locations = Locations(option.location_map)

if option.type == "s":
  print "Instantiate schools"
  insts = Schools(locations, option.source_dir, option.ks)
else:
  print "Instantiate nurseries"
  insts = Nurseries(locations, option.source_dir, option.ks)

insts.parse()

output = Output(option.output)
insts.write(output)


