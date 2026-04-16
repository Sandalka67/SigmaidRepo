document.addEventListener("DOMContentLoaded", () => {
    const mapContainer = document.getElementById('map');
    if (mapContainer) {
        window.map = L.map('map').setView([42.7339, 25.4858], 7); 
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
    }
    const emergencyBtn = document.getElementById('emergency-btn');
    if (emergencyBtn) {
        emergencyBtn.addEventListener('click', () => {
            emergencyBtn.disabled = true;
            emergencyBtn.innerText = "Locating...";

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition((position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    if (map) {
                        L.circleMarker([lat, lng], {
                            radius: 12, fillColor: "#ff0000", color: "#ffffff", weight: 2, fillOpacity: 1
                        }).addTo(map)
                          .bindPopup('<b style="color:red;">🚨 YOUR SIGNAL</b><br>Help is on the way!')
                          .openPopup();
                    }
                    if (typeof window.sendSignal === "function") {
                        window.sendSignal(lat, lng);
                    } else {
                        console.error("sendSignal function is missing! Is the second file loaded?");
                    }

                }, (error) => {
                    alert("Please enable location services to send an emergency signal.");
                    emergencyBtn.disabled = false;
                    emergencyBtn.innerText = "⚠️ EMERGENCY";
                }, { enableHighAccuracy: true });
            } else {
                alert("Geolocation is not supported by this browser.");
            }
        });
    }
});