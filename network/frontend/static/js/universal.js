var map = L.map('map',{
    center:[40.83548605,-7.99394846],
    zoom: 15
}).setView([40.83548605,-7.99394846], 15);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);