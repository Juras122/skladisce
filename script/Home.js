// Get references to the button and the table body
const dodajElementBtn = document.getElementById('dodajElementBtn');
const teloTabele = document.getElementById('teloTabele');

// Base URL for your Flask API
// IMPORTANT: You MUST replace 'YOUR_RENDER_APP_URL_HERE' with your actual Render app URL
// e.g., 'https://skladi-app.onrender.com/api'
const API_BASE_URL = 'YOUR_RENDER_APP_URL_HERE/api'; // <--- IMPORTANT: CHANGE THIS AFTER DEPLOYMENT

// Cache for storing original values during edit (to revert on cancel)
const originalValues = {}; // Stores { itemId: { ime, lokacija, komentar } }

// Variable to track the ID of the item currently being edited
let currentlyEditingItemId = null; // Initialize to null, means no item is being edited

// Helper function to append or update a row in the table
function updateOrCreateRow(item) {
    // If this row is currently being edited, skip updating its content
    if (currentlyEditingItemId === item.id) {
        // console.log(`Skipping update for item ID: ${item.id} because it's being edited.`);
        return;
    }

    let row = document.getElementById(`item-row-${item.id}`);

    if (!row) {
        // If row doesn't exist, create it
        row = document.createElement('tr');
        row.id = `item-row-${item.id}`; // Give the row an ID for easy lookup
        teloTabele.appendChild(row);
    }

    // Store original values for potential cancel operation
    originalValues[item.id] = {
        ime: item.ime,
        lokacija: item.lokacija,
        komentar: item.komentar
    };

    // Update the row's content
    row.innerHTML = `
        <td data-label="ID">${item.id}</td>
        <td data-label="Ime" class="editable-ime">${item.ime}</td>
        <td data-label="Količina">${item.kolicina}</td>
        <td data-label="Lokacija" class="editable-lokacija">${item.lokacija}</td>
        <td data-label="Komentar" class="editable-komentar">${item.komentar || ''}</td>
        <td data-label="Akcija">
            <button class="urediBtn" data-id="${item.id}">Uredi</button>
            </td>
    `;

    // Re-attach event listeners for "Uredi" on the new/updated row
    const urediBtn = row.querySelector('.urediBtn');
    urediBtn.onclick = () => startEditing(item.id);
}

// Function to start editing a row
function startEditing(itemId) {
    const row = document.getElementById(`item-row-${itemId}`);
    if (!row) return;

    // Set the currently editing item ID
    currentlyEditingItemId = itemId;

    // Get the cells to make editable
    const imeCell = row.querySelector('.editable-ime');
    const lokacijaCell = row.querySelector('.editable-lokacija');
    const komentarCell = row.querySelector('.editable-komentar');
    const actionCell = row.querySelector('[data-label="Akcija"]');

    // Store current text content to revert if cancelled
    originalValues[itemId] = {
        ime: imeCell.textContent,
        lokacija: lokacijaCell.textContent,
        komentar: komentarCell.textContent
    };

    // Replace text content with input fields
    imeCell.innerHTML = `<input type="text" value="${imeCell.textContent}" class="edit-input ime-input">`;
    lokacijaCell.innerHTML = `<input type="text" value="${lokacijaCell.textContent}" class="edit-input lokacija-input">`;
    komentarCell.innerHTML = `<input type="text" value="${komentarCell.textContent}" class="edit-input komentar-input">`;

    // Change action buttons to Save and Cancel
    actionCell.innerHTML = `
        <button class="shraniBtn" data-id="${itemId}">Shrani</button>
        <button class="prekliciBtn" data-id="${itemId}">Prekliči</button>
    `;

    // Attach new event listeners to Save and Cancel buttons
    row.querySelector('.shraniBtn').onclick = () => saveEditedItem(itemId);
    row.querySelector('.prekliciBtn').onclick = () => cancelEditing(itemId);
}

// Function to cancel editing
function cancelEditing(itemId) {
    const row = document.getElementById(`item-row-${itemId}`);
    if (!row) return;

    // Reset the currently editing item ID
    currentlyEditingItemId = null;

    // Revert to original values from cache
    const original = originalValues[itemId];
    if (original) {
        row.querySelector('.editable-ime').textContent = original.ime;
        row.querySelector('.editable-lokacija').textContent = original.lokacija;
        row.querySelector('.editable-komentar').textContent = original.komentar;
    }

    // Revert action buttons back to Uredi
    const actionCell = row.querySelector('[data-label="Akcija"]');
    actionCell.innerHTML = `
        <button class="urediBtn" data-id="${itemId}">Uredi</button>
    `;

    // Re-attach original event listener
    row.querySelector('.urediBtn').onclick = () => startEditing(itemId);

    // Immediately refresh the table to ensure other rows are up-to-date
    refreshTableData();
}

// Function to save edited item to server
async function saveEditedItem(itemId) {
    const row = document.getElementById(`item-row-${itemId}`);
    if (!row) return;

    const imeInput = row.querySelector('.ime-input');
    const lokacijaInput = row.querySelector('.lokacija-input');
    const komentarInput = row.querySelector('.komentar-input');

    const updatedData = {
        ime: imeInput.value,
        lokacija: lokacijaInput.value,
        komentar: komentarInput.value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/items/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatedData)
        });

        if (!response.ok) {
            const errorBody = await response.json();
            throw new Error(`Server error: ${response.status} - ${errorBody.error || response.statusText}`);
        }

        const result = await response.json();
        console.log('Item updated successfully:', result);
        alert('Element uspešno posodobljen!');

        // Reset the currently editing item ID
        currentlyEditingItemId = null;

        // After successful save, revert inputs back to text
        imeInput.parentNode.textContent = updatedData.ime;
        lokacijaInput.parentNode.textContent = updatedData.lokacija;
        komentarInput.parentNode.textContent = updatedData.komentar;

        // Revert action buttons back to Uredi
        const actionCell = row.querySelector('[data-label="Akcija"]');
        actionCell.innerHTML = `
            <button class="urediBtn" data-id="${itemId}">Uredi</button>
        `;
        // Re-attach event listener for the original button
        row.querySelector('.urediBtn').onclick = () => startEditing(itemId);

        // Immediately refresh the table to ensure other rows are up-to-date
        refreshTableData();

    } catch (error) {
        console.error('Napaka pri shranjevanju elementa:', error);
        alert('Napaka pri shranjevanju elementa: ' + error.message);
    }
}

// Function to fetch data from the server and update the table
async function refreshTableData() {
    // console.log('Fetching latest data...'); // Uncomment for debugging
    try {
        // IMPORTANT: Ensure API_BASE_URL is correctly set before deployment!
        const response = await fetch(`${API_BASE_URL}/items`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const items = await response.json();

        if (items.length === 0) {
            teloTabele.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 20px;">Ni podatkov o artiklih v skladišču.</td></tr>';
        } else {
            const currentTableItemIds = new Set(
                Array.from(teloTabele.children).map(row => row.id.replace('item-row-', ''))
            );

            items.forEach(item => {
                updateOrCreateRow(item); // This will handle creating new rows or updating existing ones
                currentTableItemIds.delete(item.id);
            });

            // Remove any rows that are no longer present in the fetched data
            currentTableItemIds.forEach(idToRemove => {
                // Only remove if it's NOT the row currently being edited
                if (currentlyEditingItemId !== idToRemove) {
                    const rowToRemove = document.getElementById(`item-row-${idToRemove}`);
                    if (rowToRemove) {
                        rowToRemove.remove();
                    }
                }
            });
        }

    } catch (error) {
        console.error('Napaka pri pridobivanju podatkov:', error);
        teloTabele.innerHTML = `<tr><td colspan="6" style="color: red; text-align: center; padding: 20px;">Napaka pri nalaganju podatkov: ${error.message}</td></tr>`;
    }
}

// Initial load when the page loads
document.addEventListener('DOMContentLoaded', () => {
    refreshTableData();
    // Set an interval to refresh data every 30 seconds
    setInterval(refreshTableData, 30000); // Refresh every 30 seconds
});

// "Osveži" button functionality
dodajElementBtn.addEventListener('click', () => {
    refreshTableData(); // Triggers a manual refresh
    alert("Ročna osvežitev podatkov iz senzorjev.");
});