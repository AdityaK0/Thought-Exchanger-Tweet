document.querySelector('.three-dots').addEventListener('click', function () {
    const dropdown = document.querySelector('.dropdown-content');
    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
  });
  
document.querySelector('[data-bs-toggle="offcanvas"]').addEventListener('click', function() {
    const rightPanel = document.querySelector('.right-panel');
    rightPanel.classList.toggle('open');
});
