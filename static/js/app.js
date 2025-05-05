// Photo Reminder App JavaScript

// Keep track of active reminders
let activeReminders = [];

// Update notification badge count
function updateNotificationCount() {
    const count = activeReminders.length;
    const badge = document.getElementById('notification-count');
    
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'block' : 'none';
    }
}

// Set up periodic location checking (if enabled)
let locationCheckInterval = null;

function startLocationChecking(intervalMinutes = 15) {
    // Clear any existing interval
    if (locationCheckInterval) {
        clearInterval(locationCheckInterval);
    }
    
    // Set up new interval
    locationCheckInterval = setInterval(() => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(position => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                const preferences = document.getElementById('preferences').value;
                
                // Automatically submit the form with the current location
                document.getElementById('latitude').value = lat;
                document.getElementById('longitude').value = lng;
                
                // Create FormData and submit
                const formData = new FormData();
                formData.append('latitude', lat);
                formData.append('longitude', lng);
                formData.append('preferences', preferences);
                
                fetch('/process-location', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.reminder) {
                        // Insert the new reminder HTML
                        document.getElementById('reminders-container').insertAdjacentHTML('beforeend', data.html);
                        
                        // Show browser notification
                        showNotification(data.reminder.message);
                        
                        // Add to active reminders
                        activeReminders.push(data.reminder);
                        updateNotificationCount();
                    }
                })
                .catch(error => console.error('Error checking location:', error));
            });
        }
    }, intervalMinutes * 60 * 1000); // Convert minutes to milliseconds
    
    console.log(`Location checking started (every ${intervalMinutes} minutes)`);
}

// Function to enable background tracking
function enableBackgroundTracking() {
    // Check if browser supports notifications
    if ("Notification" in window) {
        Notification.requestPermission().then(permission => {
            if (permission === "granted") {
                // Start location checking
                startLocationChecking(15); // Check every 15 minutes
                
                // Update UI to show tracking is enabled
                const trackingStatus = document.getElementById('tracking-status');
                if (trackingStatus) {
                    trackingStatus.textContent = 'Background tracking enabled';
                    trackingStatus.classList.remove('bg-yellow-500');
                    trackingStatus.classList.add('bg-green-500');
                }
            }
        });
    }
}

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up tracking toggle button
    const trackingButton = document.getElementById('toggle-tracking');
    if (trackingButton) {
        trackingButton.addEventListener('click', enableBackgroundTracking);
    }
    
    // Update notification count on page load
    updateNotificationCount();
});

// Event delegation for dismissing reminders
document.addEventListener('click', function(event) {
    if (event.target.matches('[data-dismiss-reminder]') || 
        event.target.closest('[data-dismiss-reminder]')) {
        
        const button = event.target.matches('[data-dismiss-reminder]') ? 
                       event.target : 
                       event.target.closest('[data-dismiss-reminder]');
        
        const reminderId = button.getAttribute('data-reminder-id');
        
        // Remove from active reminders
        activeReminders = activeReminders.filter(r => r.id !== parseInt(reminderId));
        updateNotificationCount();
    }
});