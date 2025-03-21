
function togglePopup() {
    const overlay = document.getElementById('popupOverlay');
    overlay.classList.toggle('show');
}


// Open Modal
function openModal() {
    const modal = document.getElementById('tweetModal');
    modal.style.display = 'flex'; // Make it visible
  }
  
  // Close Modal
  function closeModal() {
    const modal = document.getElementById('tweetModal');
    modal.style.display = 'none'; // Hide it
  }
  
  // Close Modal on Outside Click
  window.onclick = function (event) {
    const modal = document.getElementById('tweetModal');
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  };
  