let CONFIG = {
    colour_endpoint:"https://octoprice.onrender.com/colour",
    help_endpoint:"https://octoprice.onrender.com/requesthelp",
    helpData:{
      "time": "2024-11-10T22:02:39.640Z",
      "from_device_id": "10",
      "tel": "+000000001"
      },
    checkInterval: 1 * 60 * 1000
    };

let green = [0,100,0]; 
let red = [100,0,0];
let yellow  = [100,100,0];
let blue = [0,0,100];

let current_colour = yellow;
let lastPressTime = null;

Shelly.addEventHandler(function(event) {
  if (event.component === "switch:0") {
    Shelly.call("Sys.GetStatus", {}, function(result, error_code) {
      if (error_code === 0 && result) {
        let currentTime = result.uptime;
        if (lastPressTime && (currentTime - lastPressTime) < 1) {
          // Double press detected
          print("Double press detected... making HTTP call");
          updateColour(blue, true);
          requestHelp(CONFIG.helpData)
          
          lastPressTime = null; // Reset for next detection
        } else {
          // Single press action
          print("Single press detected");
          lastPressTime = currentTime;
        }
      } else {
        print("Error retrieving button press timings");
      }
    });
  }
});


// Define a function to handle the HTTP PUT request
function requestHelp(data) {
  Shelly.call(
    "http.request",
    {method:"PUT", url:"https://octoprice.onrender.com/requesthelp", body: JSON.stringify(data)},
    function (result, error_code, error_message) {
      if (error_code === 0) {
        // Successful response
        print("Error Code 0");
        print("Response data:", JSON.stringify(result.body));
      } else {
        // Handle errors
        print("PUT request failed with error code:", error_code);
        if (error_code === 408) {
          print("Error: Request timed out.");
        } else if (error_code === 404) {
          print("Error: Endpoint not found (404).");
        } else {
          print("Error message:", error_message);
        }
      }
    }
  );
}


function updateColour(colour, flag) {
   Shelly.call("PLUGUK_UI.SetConfig", {
    'id': 0,
    'config': {
          'leds': {
          'mode': 'switch', 
          'colors': {
              'switch:0': {
                  'on': {
                      'rgb': colour,
                      'brightness': 100
                  },
                  'off': {
                      'rgb': colour,
                      'brightness': 100
                  }   
              },
              'power': {'brightness': 100}
          }
        }      
    }
  }, function(res) {
    if (res) {
      print(flag);
      //Put colour transition in here... (if needed)
    }
  });
 }


function getOctoData() {
  console.log("Gettting Data from: " + CONFIG.colour_endpoint);
  Shelly.call(
      "http.get", {url: CONFIG.colour_endpoint}, function (response, error_code, error_message) {
        if (error_code === 0) {
          if (response.code == 200){
            let jbody = JSON.parse(response.body);
            print("HTTP Status: " + response.code);
            print("colour: "+jbody.colour);
            if (jbody.colour === "red") {
              updateColour(red, false);
              print("updated to red");
            } else if (jbody.colour === "yellow") {
              updateColour(yellow, false);
              print("updated to yellow");
            } else if (jbody.colour === "green") {
              updateColour(green, false);
              print("updated to green");
            } else {
              updateColour(blue, false);
              print("updated to blue");
            }}
        } else {
          updateColour(blue, false);
          print("Error Getting Data");
        }
    },
  );
}

//watch out for async things going on... need to use callbacks or nested calls to get the sequence right...
Timer.set(CONFIG.checkInterval, true, function () {
  getOctoData();
});
