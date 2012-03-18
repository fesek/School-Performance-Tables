

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
