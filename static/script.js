document.addEventListener('DOMContentLoaded', () => {
    const fleetTableBody = document.getElementById('fleet-table-body');
    const distanceInput = document.getElementById('distance-input');
    const trafficInput = document.getElementById('traffic-input');
    const optimizeBtn = document.getElementById('optimize-btn');
    const resultsBox = document.getElementById('results-box');
    const resHours = document.getElementById('res-hours');
    const resSpeed = document.getElementById('res-speed');

    // FETCH ACTIVE FLEET DATA (GET)
    function fetchFleetData() {
        fetch('/api/fleet')
        .then(response => response.json())
        .then(data => {
            fleetTableBody.innerHTML = '';
            // FIXED: Fixed the typo from forEaach to forEach
            data.forEach(truck => {
                let statusColor = "bg-gray-100 text-gray-800";
                if (truck.status === "In Transit") statusColor = "bg-blue-100 text-blue-800";
                if (truck.status === "Delivered") statusColor = "bg-green-100 text-green-800";
                if (truck.status === "Delayed") statusColor = "bg-red-100 text-red-800";
                
                // FIXED: Wrapped the HTML block in proper backticks (``) and fixed hover:bg-gray-50
                const rowHTML = `
                <tr class="hover:bg-gray-50 transition">
                    <td class="p-3 font-semibold text-blue-600">${truck.truck_id}</td>
                    <td class="p-3">${truck.driver}</td>
                    <td class="p-3">
                        <span class="px-2.5 py-1 rounded text-xs font-medium ${statusColor}">
                            ${truck.status}
                        </span>
                    </td>
                    <td class="p-3">${truck.destination}</td>
                    <td class="p-3 text-right font-medium text-green-600">${truck.fuel_efficiency}</td>
                </tr>`;
                
                fleetTableBody.innerHTML += rowHTML;
            });
        })
        .catch(error => {
            console.error("Error loading fleet data:", error);
            // FIXED: Fixed structural td html tag closure bug
            fleetTableBody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-red-500 font-semibold">Failed to connect to Python backend server.</td></tr>';
        });
    }

    // COMPUTE OPTIMIZATION
    optimizeBtn.addEventListener('click', () => {
        // FIXED: Changed .ariaValueMax to standard .value
        const distanceValue = distanceInput.value;
        const trafficValue = trafficInput.value;
        
        if (!distanceValue || distanceValue <= 0) {
            alert("Please input a valid distance greater than 0 km.");
            return;
        }
        
        const requestPayload = {
            distance: distanceValue,
            traffic: trafficValue
        };
        
        fetch('/api/optimize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestPayload)
        })
        .then(response => response.json())
        .then(result => {
            resHours.innerText = result.estimated_hours;
            resSpeed.innerText = result.recommended_speed;
            resultsBox.classList.remove('hidden');
        })
        .catch(error => {
            console.error("Optimization failed:", error);
            alert("An error occurred while communicating with the analytics engine.");
        });
    });

    fetchFleetData();
});