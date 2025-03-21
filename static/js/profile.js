function showPopup(type) {
    document.getElementById(`${type}-popup`).style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function hidePopup(type) {
    document.getElementById(`${type}-popup`).style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Close popup when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('popup-overlay')) {
        event.target.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}