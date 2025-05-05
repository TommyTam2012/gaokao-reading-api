/**
 * Main script for the TommySir's 高考阅读、语法 AI辅助考试练习 application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application when the DOM is fully loaded
    initApp();
});

/**
 * Initialize the application components
 */
function initApp() {
    console.log('Application initialized');
    
    // Add event listeners to buttons
    const startButton = document.querySelector('.btn-primary');
    if (startButton) {
        startButton.addEventListener('click', function(e) {
            console.log('Start button clicked');
        });
    }
    
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Check if the API service is available
    checkApiAvailability();
}

/**
 * Check if the API service is available
 */
async function checkApiAvailability() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        if (data.status === 'ok') {
            console.log('API service is available');
        } else {
            console.warn('API service status warning:', data.message);
        }
    } catch (error) {
        console.error('API service is not available:', error);
    }
}

/**
 * Add a glowing effect that follows the mouse
 */
document.addEventListener('mousemove', function(e) {
    const glowElement = document.querySelector('.glow');
    if (glowElement) {
        // Only update every few frames for performance
        if (Math.random() > 0.9) {
            glowElement.style.top = e.pageY + 'px';
            glowElement.style.left = e.pageX + 'px';
            glowElement.style.transform = 'translate(-50%, -50%)';
        }
    }
});
