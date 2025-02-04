let CONFIG = {
  colour_endpoint:"https://octoprice.onrender.com/colour",
  help_endpoint:"https://octoprice.onrender.com/requesthelp",
  helpData:{
    "time": "2024-11-10T22:02:39.640Z", // To be removed and replaced with server-side timestamp
    "from_device_id": "10", // Yet to be implemented
    "tel": "+440000000000" // Needs to be UK number, starting with 44 and having a total of 12 digits
    },
  checkInterval: 1 * 60 * 1000,
  wa_api_key: "Not_Implemented",
  };

let green = [0,100,0]; 
let red = [100,0,0];
let yellow  = [100,100,0];
let blue = [0,0,100];
let purple = [100,0,100]; 

let current_colour = yellow;
let lastPressTime = null;

let pressCount = 0;
let pressTimer = null;
let doublePressTimeout = 2000;  // 3 seconds window for detecting double press

Shelly.addStatusHandler(function(status) {
  if (status.component === "switch:0" && status.delta.output !== undefined) {
      pressCount++;

      if (pressCount === 1) {
          // Start a timer for detecting a second press
          pressTimer = Timer.set(doublePressTimeout, false, function() {
              print("Single press detected!");
              // Perform no action for single press
              // Reset after timeout
              pressCount = 0;
              pressTimer = null;
          });
      } else if (pressCount === 2) {
          // Second press detected before timer expired -> it's a double press!
          print("Double press detected... making HTTP call");          
          requestHelp(CONFIG.helpData)
          updateColour(purple, true);
          //CONFIG.helpData.from_device_id = result.mac

          // Clear the single-press timer since we now have a double press
          Timer.clear(pressTimer);
          pressCount = 0;
          pressTimer = null;
      }
  }
});

// *************** Only required for Mac ID ***************8
//function getTime() {
//  Shelly.call("Sys.GetStatus", {}, function(result) {
//    if (result) {
//      CONFIG.helpData.from_device_id = result.mac
//    } else {
//      CONFIG.helpData.from_device_id = 0
//    }
//  })
//}


// Function to handle the HTTP PUT request for Help
function requestHelp(data) {
Shelly.call(
  "http.request",
  {method:"PUT", url:"https://octoprice.onrender.com/requesthelp", headers:{"wa_api_key": CONFIG.wa_api_key}, body: JSON.stringify(data)},
  function (result, error_code, error_message) {
    if (error_code === 0) {
      // Successful response
      // print(result.code);
      print("Response data:", JSON.stringify(result.body));
    } else {
      // Handle errors
      print("PUT request failed with error code:", error_code);
      print("Error message:", error_message);
    }
  }
);
}

// Function to update the LED colour on the plug.
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
    print("update colour flag: ", flag);
    // Not Implemented -> Put colour transition in here... if needed
  }
});
}

// Function to get the latest price colour from API and request the LED colour change.
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
        updateColour(purple, false);
        print("Error Getting Data");
      }
  },
);
}

// Timer to re-run the getOctoData() function at a regular interval to check for updates and changes
Timer.set(CONFIG.checkInterval, true, function () {
getOctoData();
});
