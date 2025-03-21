const usernameInput = document.getElementById('username-input');
const suggestionsDatalist = document.getElementById('username-suggestions');

usernameInput.addEventListener('input', () => {
    const query = usernameInput.value;

    if (query.length > 0) {
        fetch(`/suggest-users/?username=${query}`)
            .then(response => response.json())
            .then(data => {
                suggestionsDatalist.innerHTML = '';  // Clear previous suggestions
                console.log(data)
                // Populate datalist with new suggestions
                data.forEach(user => {
                    const option = document.createElement('option');
                    option.value = user.username; // Set the value for each suggestion
                    suggestionsDatalist.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error fetching suggestions:', error);
            });
    } else {
        suggestionsDatalist.innerHTML = '';  // Clear suggestions if input is empty
    }
});
