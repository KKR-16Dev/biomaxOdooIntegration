/** @odoo-module **/

let map;
let marker;

function initializeLocationCapture() {
    if (document.getElementById('dailySubmissionForm')) {
        captureCurrentLocation();
        initializeMap();
        setupFormSubmission();
    }
}

function captureCurrentLocation() {
    if (!navigator.geolocation) {
        showAlert('Geolocation is not supported by your browser.', 'warning');
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;
            
            // Set the values in the form
            document.getElementById('latitude').value = latitude.toFixed(7);
            document.getElementById('longitude').value = longitude.toFixed(7);
            
            // Update map
            updateMap(latitude, longitude);
            
            showAlert('Location captured successfully!', 'success');
        },
        (error) => {
            let errorMessage = 'Unable to retrieve your location.';
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage = 'Location permission denied. Please enable location access.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage = 'Location information is unavailable.';
                    break;
                case error.TIMEOUT:
                    errorMessage = 'Location request timed out.';
                    break;
            }
            showAlert(errorMessage, 'warning');
            console.error('Geolocation error:', error);
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

function initializeMap() {
    // Default location (will be updated when location is captured)
    const defaultLat = 12.9716;
    const defaultLng = 77.5946;
    
    const mapOptions = {
        center: { lat: defaultLat, lng: defaultLng },
        zoom: 15,
        mapTypeId: 'roadmap'
    };
    
    map = new google.maps.Map(document.getElementById('map'), mapOptions);
    
    marker = new google.maps.Marker({
        position: { lat: defaultLat, lng: defaultLng },
        map: map,
        title: 'Your Location',
        icon: {
            url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png'
            // url: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
        }
    });
}

function updateMap(lat, lng) {
    const position = { lat: lat, lng: lng };
    
    if (map && marker) {
        map.setCenter(position);
        marker.setPosition(position);
        
        // Update "View larger map" link
        // const mapsUrl = `https://www.google.com/maps?q=${lat},${lng}`;
        const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
        document.getElementById('viewLargerMap').href = mapsUrl;
    }
}

function setupFormSubmission() {
    const form = document.getElementById('dailySubmissionForm');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('name').value,
            // phone: document.getElementById('phone').value,
            // email: document.getElementById('email').value,
            // company: document.getElementById('company').value,
            // subject: document.getElementById('subject').value,
            // latitude: document.getElementById('latitude').value,
            // longitude: document.getElementById('longitude').value,

            crane_name: document.getElementById('crane_name').value,
            x_date_time: document.getElementById('x_date_time').value,
            customer_name: document.getElementById('customer_name').value,
            customer_mobile_number: document.getElementById('customer_mobile_number').value,
            operator_name: document.getElementById('operator_name').value,
            start_time: document.getElementById('start_time').value,
            close_time: document.getElementById('close_time').value,
            lunch: document.getElementById('lunch').value,
            working_photo: document.getElementById('working_photo').value,
            payment: document.getElementById('payment').value,
            operator_selfie: document.getElementById('operator_selfie').value,
            work_nature: document.getElementById('work_nature').value,
            operator_beta: document.getElementById('operator_beta').value,
            logsheet_picture: document.getElementById('logsheet_picture').value,
            comments_work: document.getElementById('comments_work').value,
            work_assigned_by: document.getElementById('work_assigned_by').value,
            shift_confirmed: document.getElementById('shift_confirmed').value,
            fill_diesel: document.getElementById('fill_diesel').value,

            operator_signature: document.getElementById('operator_signature').value,
            customer_signature: document.getElementById('customer_signature').value,
            
        };
        
        // Validate location
        if (!formData.latitude || !formData.longitude) {
            showAlert('Please allow location access to submit the form.', 'danger');
            captureCurrentLocation(); // Try again
            return;
        }
        
        try {
            const response = await fetch('/daily-submission/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: formData
                })
            });
            
            const result = await response.json();
            
            if (result.result && result.result.success) {
                showAlert(result.result.message, 'success');
                setTimeout(() => {
                    window.location.href = '/daily-submission/thank-you';
                }, 1500);
            } else {
                showAlert(result.result.message || 'Submission failed. Please try again.', 'danger');
            }
        } catch (error) {
            console.error('Submission error:', error);
            showAlert('An error occurred. Please try again.', 'danger');
        }
    });
}

function showAlert(message, type) {
    const alertDiv = document.getElementById('alertMessage');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    alertDiv.style.display = 'block';
    
    setTimeout(() => {
        alertDiv.style.display = 'none';
    }, 5000);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeLocationCapture);
} else {
    initializeLocationCapture();
}