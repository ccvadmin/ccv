let vehicleLocation;
let warehouseLocation
let destinationLocation

const origin = window.location.origin;
const current_url = window.location.search;
function getLocation() {
    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        function(position) {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          resolve({ lat, lng });
        },
        function(error) {
          reject('Error occurred: ' + error.message);
        },
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 0
        }
      );
    });
  }
  
function getUrlParameter(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

async function postPosition() {
	await changeMarkerPosition(vehicleMarker)
    const pathname = '/public/order/set-location';
    const url = `${origin}${pathname}${current_url}&lat=${vehicleLocation.lat}&lng=${vehicleLocation.lng}`;

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
        });

        if (response.ok) {
            const data = await response.json();
            console.log(data);
        } else {
            console.error("Request failed with status:", response.status);
        }
    } catch (error) {
        console.error("Error posting position:", error);
    }
}


async function getPosition() {
    const pathname = '/public/order/get-location';
    const url = `${origin}${pathname}${current_url}`;
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.status === 0) {
                vehicleLocation = data.locations.current;
                if (destinationLocation === undefined)
                    destinationLocation = data.locations.dest;
                if (warehouseLocation === undefined)
                    warehouseLocation = data.locations.src;
            } else {
                console.error(data.message);
            }
        } else {
            console.error("Request failed with status:", response.status);
        }
    } catch (error) {
        console.error("Error getting position:", error);
    }
}


function checkLocation(location) {
    if (location == undefined)
        return false
    if (location.lat == 0 || location.lng == 0)
        return false
    return true
}
