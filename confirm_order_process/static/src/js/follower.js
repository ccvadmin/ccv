let map;
let directionsService;
let directionsRenderer;
let vehicleMarker;
let vehicleMarker1;
let vehicleMarker2;
let vehicleMarker3;
let vehicleMarker4;
let destinationMarker;
let warehouseMarker;

const house_icon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48px" height="48px"><linearGradient id="jv689zNUBazMNK6AOyXtga" x1="6" x2="42" y1="41" y2="41" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#c8d3de"/><stop offset="1" stop-color="#c8d3de"/></linearGradient><path fill="url(#jv689zNUBazMNK6AOyXtga)" d="M42,39H6v2c0,1.105,0.895,2,2,2h32c1.105,0,2-0.895,2-2V39z"/><linearGradient id="jv689zNUBazMNK6AOyXtgb" x1="14.095" x2="31.385" y1="10.338" y2="43.787" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#fcfcfc"/><stop offset=".495" stop-color="#f4f4f4"/><stop offset=".946" stop-color="#e8e8e8"/><stop offset="1" stop-color="#e8e8e8"/></linearGradient><path fill="url(#jv689zNUBazMNK6AOyXtgb)" d="M42,39H6V20L24,3l18,17V39z"/><path fill="#de490d" d="M13,25h10c0.552,0,1,0.448,1,1v17H12V26C12,25.448,12.448,25,13,25z"/><path d="M24,4c-0.474,0-0.948,0.168-1.326,0.503l-5.359,4.811L6,20v5.39L24,9.428L42,25.39V20L30.685,9.314 l-5.359-4.811C24.948,4.168,24.474,4,24,4z" opacity=".05"/><path d="M24,3c-0.474,0-0.948,0.167-1.326,0.5l-5.359,4.784L6,18.909v5.359L24,8.397l18,15.871v-5.359 L30.685,8.284L25.326,3.5C24.948,3.167,24.474,3,24,3z" opacity=".07"/><linearGradient id="jv689zNUBazMNK6AOyXtgc" x1="24" x2="24" y1="1.684" y2="23.696" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#d43a02"/><stop offset="1" stop-color="#b9360c"/></linearGradient><path fill="url(#jv689zNUBazMNK6AOyXtgc)" d="M44.495,19.507L25.326,2.503C24.948,2.168,24.474,2,24,2s-0.948,0.168-1.326,0.503 L3.505,19.507c-0.42,0.374-0.449,1.02-0.064,1.43l1.636,1.745c0.369,0.394,0.984,0.424,1.39,0.067L24,7.428L41.533,22.75 c0.405,0.356,1.021,0.327,1.39-0.067l1.636-1.745C44.944,20.527,44.915,19.881,44.495,19.507z"/><linearGradient id="jv689zNUBazMNK6AOyXtgd" x1="28.05" x2="35.614" y1="25.05" y2="32.614" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#33bef0"/><stop offset="1" stop-color="#0a85d9"/></linearGradient><path fill="url(#jv689zNUBazMNK6AOyXtgd)" d="M29,25h6c0.552,0,1,0.448,1,1v6c0,0.552-0.448,1-1,1h-6c-0.552,0-1-0.448-1-1v-6 C28,25.448,28.448,25,29,25z"/></svg>`;
const warehouse_icon = `<?xml version="1.0" encoding="iso-8859-1"?>
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" 
	 viewBox="0 0 512 512" xml:space="preserve">
<polygon style="fill:#D4D4D4;" points="105.086,80.156 52.544,80.156 31.644,154.956 105.086,134.057 "/>
<polygon style="fill:#EDEDED;" points="0,80.156 0,134.057 52.544,154.956 52.544,80.156 "/>
<polygon style="fill:#D61322;" points="512,166.398 376.362,220.57 376.362,166.398 256,214.468 235.101,320.784 256,431.844 
	512,431.844 "/>
<polygon style="fill:#EC2533;" points="240.725,220.57 240.725,166.398 105.086,220.57 105.086,134.057 0,134.057 0,431.844 
	256,431.844 256,214.468 "/>
<polygon style="fill:#FF9500;" points="178.875,289.886 141.981,289.886 121.082,326.779 141.981,363.673 178.875,363.673 "/>
<rect x="105.085" y="289.886" style="fill:#FFC222;" width="36.895" height="73.791"/>
<polygon style="fill:#FF9500;" points="314.512,289.886 277.619,289.886 256.719,326.779 277.619,363.673 314.512,363.673 "/>
<rect x="240.724" y="289.886" style="fill:#FFC222;" width="36.895" height="73.791"/>
<polygon style="fill:#FF9500;" points="450.15,289.886 413.256,289.886 392.357,326.779 413.256,363.673 450.15,363.673 "/>
<rect x="376.362" y="289.886" style="fill:#FFC222;" width="36.895" height="73.791"/>
</svg>`;
const truck_icon = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 1024 1024" class="icon" version="1.1"><path d="M425.176 123.4h554.432v424.992H425.176z" fill="#E6246B"/><path d="M893.832 809.152c47.384 0 85.784-38.392 85.784-85.784V543.624H425.976V241.288l-234.064-0.768L40.92 492.192V723.36c0 47.392 38.392 85.784 85.752 85.784h767.16z" fill="#F6B246"/><path d="M893.832 809.152c47.384 0 85.784-38.392 85.784-85.784V603.832H40.92V723.36c0 47.392 38.392 85.784 85.752 85.784h767.16z" fill="#ECD4BE"/><path d="M853.728 824.552c0 56.152-45.504 101.592-101.6 101.592-56.152 0-101.592-45.448-101.592-101.592 0-56.096 45.448-101.6 101.592-101.6 56.088 0 101.6 45.512 101.6 101.6zM379.584 824.552c0 56.152-45.48 101.592-101.6 101.592s-101.6-45.448-101.6-101.592c0-56.096 45.48-101.6 101.6-101.6s101.6 45.512 101.6 101.6z" fill="#0093D3"/><path d="M264.192 454.568H62.848l109.128-178.736h92.216z" fill="#E09431"/></svg>`;

async function changeMarkerPosition() {
	await getPosition()
	if (vehicleMarker != undefined) {
		let v_index = 0
		var newLatLng = new google.maps.LatLng(vehicleLocation[v_index].lat, vehicleLocation[v_index].lng);
		vehicleMarker.setPosition(newLatLng);

		v_index = 1
		if (vehicleLocation.length > v_index) {
			var newLatLng = new google.maps.LatLng(vehicleLocation[v_index].lat, vehicleLocation[v_index].lng);
			vehicleMarker1.setPosition(newLatLng);
		}
		v_index = 2
		if (vehicleLocation.length > v_index) {
			var newLatLng = new google.maps.LatLng(vehicleLocation[v_index].lat, vehicleLocation[v_index].lng);
			vehicleMarker2.setPosition(newLatLng);
		}
		v_index = 3
		if (vehicleLocation.length > v_index) {
			var newLatLng = new google.maps.LatLng(vehicleLocation[v_index].lat, vehicleLocation[v_index].lng);
			vehicleMarker3.setPosition(newLatLng);
		}
		v_index = 4
		if (vehicleLocation.length > v_index) {
			var newLatLng = new google.maps.LatLng(vehicleLocation[v_index].lat, vehicleLocation[v_index].lng);
			vehicleMarker4.setPosition(newLatLng);
		}
	}

}

async function initMap() {
	await changeMarkerPosition()
	const warehouseIcon = {
		url: `data:image/svg+xml;utf-8,${encodeURIComponent(warehouse_icon)}`,
		scaledSize: new google.maps.Size(32, 32),
	};
	const destinationIcon = {
		url: `data:image/svg+xml;utf-8,${encodeURIComponent(house_icon)}`,
		scaledSize: new google.maps.Size(32, 32),
	};
	const vehicleIcon = {
		url: `data:image/svg+xml;utf-8,${encodeURIComponent(truck_icon)}`,
		scaledSize: new google.maps.Size(32, 32),
	};

	setInterval(changeMarkerPosition, 10000);

	// Khởi tạo bản đồ
	let center = checkLocation(vehicleLocation[0]) ? { lat: vehicleLocation[0].lat, lng: vehicleLocation[0].lng } : destinationLocation
	map = new google.maps.Map(document.getElementById('map'), {
		center: center,
		zoom: 14
	});

	// Khởi tạo dịch vụ chỉ đường
	directionsService = new google.maps.DirectionsService();
	directionsRenderer = new google.maps.DirectionsRenderer({
		markerOptions: {
			visible: false,
		},
	});
	directionsRenderer.setMap(map);

	// Đánh dấu kho
	warehouseMarker = new google.maps.Marker({
		position: warehouseLocation,
		map: map,
		title: 'Kho',
		icon: warehouseIcon,
		draggable: false,
	});

	// Đánh dấu xe
	let v_index = 0
	vehicleMarker = new google.maps.Marker({
		position: { lat: vehicleLocation[v_index].lat, lng: vehicleLocation[v_index].lng },
		map: map,
		title: `Vị trí Xe ${vehicleLocation[v_index].num}`,
		icon: vehicleIcon,
		draggable: false,
	});

	v_index = 1
	if (vehicleLocation.length > v_index)
		vehicleMarker1 = new google.maps.Marker({
			position: { lat: vehicleLocation[v_index].lat, lng: vehicleLocation[v_index].lng },
			map: map,
			title: `Vị trí Xe ${vehicleLocation[v_index].num}`,
			icon: vehicleIcon,
			draggable: false,
		});

	v_index = 2
	console.log(vehicleLocation.length)
	if (vehicleLocation.length > v_index)
		vehicleMarker2 = new google.maps.Marker({
			position: { lat: vehicleLocation[v_index].lat, lng: vehicleLocation[v_index].lng },
			map: map,
			title: `Vị trí Xe ${vehicleLocation[v_index].num}`,
			icon: vehicleIcon,
			draggable: false,
		});

	v_index = 3
	if (vehicleLocation.length > v_index)
		vehicleMarker3 = new google.maps.Marker({
			position: { lat: vehicleLocation[v_index].lat, lng: vehicleLocation[v_index].lng },
			map: map,
			title: `Vị trí Xe ${vehicleLocation[v_index].num}`,
			icon: vehicleIcon,
			draggable: false,
		});

	v_index = 4
	if (vehicleLocation.length > v_index)
		vehicleMarker4 = new google.maps.Marker({
			position: { lat: vehicleLocation[v_index].lat, lng: vehicleLocation[v_index].lng },
			map: map,
			title: `Vị trí Xe ${vehicleLocation[v_index].num}`,
			icon: vehicleIcon,
			draggable: false,
		});

	// Đánh dấu điểm đến
	destinationMarker = new google.maps.Marker({
		position: destinationLocation,
		map: map,
		title: 'Điểm đến',
		icon: destinationIcon,
		draggable: false,
	});
	calculateRoute({ lat: vehicleLocation[0].lat, lng: vehicleLocation[0].lng }, destinationLocation);
}

function calculateRoute(origin, destination) {
	if (!checkLocation(origin) || !checkLocation(destination))
		return
	const request = {
		origin: origin,
		destination: destination,
		travelMode: google.maps.TravelMode.DRIVING // Chỉ đường theo chế độ lái xe
	};

	directionsService.route(request, function (result, status) {
		if (status === google.maps.DirectionsStatus.OK) {
			// Hiển thị chỉ đường trên bản đồ
			directionsRenderer.setDirections(result);

			// Lấy thông tin khoảng cách và thời gian
			const distance = result.routes[0].legs[0].distance.text; // Khoảng cách
			const duration = result.routes[0].legs[0].duration.text; // Thời gian

			// Hiển thị khoảng cách và thời gian lên giao diện
			document.getElementById('distance').innerText = distance;
			document.getElementById('duration').innerText = duration;
		} else {
			console.error("Error calculating route:", status);
		}
	});
}

window.onload = initMap;