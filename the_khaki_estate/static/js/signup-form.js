/**
 * JavaScript functionality for the new user signup form.
 * 
 * This script handles the dynamic form behavior for the improved signup workflow:
 * 1. Shows/hides fields based on user type selection
 * 2. Provides flat number autocomplete for owners
 * 3. Auto-populates fields when flat number is selected
 * 4. Handles form validation and user experience
 */

// Global variables to store available flats data
let availableFlats = [];
let filteredFlats = [];

// Initialize the form when the page loads using jQuery
$(document).ready(function() {
    console.log('Signup form JavaScript loaded');

    // Load available flats data
    loadAvailableFlats();

    // Set up event listeners
    setupEventListeners();

    // Initialize form state
    initializeFormState();
});

/**
 * Load available flats data from the server.
 * This fetches all flats that don't have associated users yet.
 */
function loadAvailableFlats() {
    console.log('Loading available flats from API...');
    fetch('/backend/api/flats/available/')
        .then(response => {
            console.log('API response status:', response.status);
            return response.json();
        })
        .then(data => {
            availableFlats = data.flats || [];
            console.log('Loaded available flats:', availableFlats.length, 'flats');
            console.log('Sample flats:', availableFlats.slice(0, 3));
        })
        .catch(error => {
            console.error('Error loading available flats:', error);
            // Fallback: create some sample data for testing
            availableFlats = [
                { id: 1, flat_number: 'A-101', block: 'A', owner_name: 'Meeraj Khalid', email: 'merajkhalidips@gmail.com', phone: '+919836293377' },
                { id: 2, flat_number: 'A-102', block: 'A', owner_name: 'Ishani Paul', email: 'ishanipaul@gmail.com', phone: '+919989702225' },
                { id: 3, flat_number: 'B-101', block: 'B', owner_name: 'Amit Javalgi', email: 'amitpjavalgi@gmail.com', phone: '+919547963285' },
                { id: 4, flat_number: 'C1-201', block: 'C1', owner_name: 'Ajay Kumar Thakur', email: 'ajay956@gmail.com', phone: '+919051500356' },
                { id: 5, flat_number: 'D-301', block: 'D', owner_name: 'Alok Rajoria', email: 'akrajoriaips@gmail.com', phone: '+919051217042' },
                // Add more sample data as needed
            ];
            console.log('Using fallback data:', availableFlats.length, 'flats');
        });
}

/**
 * Set up all event listeners for the form.
 */
function setupEventListeners() {
    console.log('Setting up event listeners...');

    // User type change handler
    $('#id_user_type').on('change', handleUserTypeChange);
    console.log('User type change handler added');

    // Resident type change handler
    $('#id_resident_type').on('change', handleResidentTypeChange);
    console.log('Resident type change handler added');

    // Flat number input handler
    $('#id_flat_number').on('input', filterFlatNumbers);
    $('#id_flat_number').on('blur', fetchResidentData);
    $('#id_flat_number').on('focus', showFlatSuggestions);
    console.log('Flat number event listeners added');

    // Add click handler for suggestions
    $(document).on('click', function(event) {
        const flatNumberInput = $('#id_flat_number')[0];
        const suggestionsContainer = $('#flat-suggestions')[0];

        if (flatNumberInput && suggestionsContainer) {
            if (!flatNumberInput.contains(event.target) && !suggestionsContainer.contains(event.target)) {
                hideFlatSuggestions();
            }
        }
    });
}

/**
 * Initialize the form state based on current values.
 */
function initializeFormState() {
    const userType = $('#id_user_type').val();
    const residentType = $('#id_resident_type').val();

    handleUserTypeChange();
    if (userType === 'resident') {
        handleResidentTypeChange();
    }
}

/**
 * Handle user type selection change.
 * Shows/hides relevant fields based on user type.
 */
function handleUserTypeChange() {
    const userType = $('#id_user_type').val();
    const residentFields = $('.resident-field');
    const dynamicFields = $('.dynamic-field');

    if (userType === 'resident') {
        // Show resident-specific fields
        residentFields.show();

        // Show dynamic fields for tenants/family
        dynamicFields.show();

        // Make resident type required
        $('#id_resident_type').prop('required', true);

    } else if (userType === 'staff') {
        // Hide resident-specific fields
        residentFields.hide();

        // Show dynamic fields for staff
        dynamicFields.show();

        // Make resident type not required
        $('#id_resident_type').prop('required', false);

    } else {
        // Hide all conditional fields
        residentFields.hide();
        dynamicFields.hide();

        // Make resident type not required
        $('#id_resident_type').prop('required', false);
    }
}

/**
 * Handle resident type selection change.
 * Shows/hides owner-specific fields.
 */
function handleResidentTypeChange() {
    const residentType = $('#id_resident_type').val();
    const ownerFields = $('.owner-field');

    if (residentType === 'owner') {
        console.log('Owner selected, showing owner fields');
        // Show owner-specific fields
        ownerFields.show();

        // Make flat number required for owners
        $('#id_flat_number').prop('required', true);

        // Set up flat number autocomplete
        console.log('Setting up autocomplete for owner');
        setupFlatNumberAutocomplete();

    } else {
        // Hide owner-specific fields
        ownerFields.hide();

        // Make flat number not required for tenants/family
        $('#id_flat_number').prop('required', false);

        // Clear any populated data
        clearAutoPopulatedData();
    }
}

/**
 * Set up autocomplete functionality for flat number input.
 */
function setupFlatNumberAutocomplete() {
    const $flatNumberInput = $('#id_flat_number');
    console.log('Setting up autocomplete for:', $flatNumberInput);

    // Create suggestions container
    let $suggestionsContainer = $('#flat-suggestions');
    if ($suggestionsContainer.length === 0) {
        $suggestionsContainer = $('<div>')
            .attr('id', 'flat-suggestions')
            .addClass('flat-suggestions')
            .css({
                'position': 'absolute',
                'background': 'white',
                'border': '2px solid red',
                'border-top': 'none',
                'max-height': '200px',
                'overflow-y': 'auto',
                'z-index': '1000',
                'width': '100%',
                'box-shadow': '0 2px 5px rgba(0,0,0,0.2)',
                'display': 'none'
            });

        // Make the parent container relative positioned
        const $parentContainer = $flatNumberInput.closest('.mb-3');
        if ($parentContainer.length > 0) {
            $parentContainer.css('position', 'relative');
            $parentContainer.append($suggestionsContainer);
            console.log('Added suggestions container to parent');
        } else {
            console.log('Could not find parent container');
        }
    }
}

/**
 * Filter flat numbers based on user input.
 */
function filterFlatNumbers() {
    const query = $('#id_flat_number').val().toLowerCase();

    console.log('Filtering flats for query:', query);
    console.log('Available flats count:', availableFlats.length);

    if (query.length < 1) {
        hideFlatSuggestions();
        return;
    }

    // Filter available flats
    filteredFlats = availableFlats.filter(flat =>
        flat.flat_number.toLowerCase().includes(query) ||
        flat.owner_name.toLowerCase().includes(query)
    );

    console.log('Filtered flats count:', filteredFlats.length);
    console.log('Filtered flats:', filteredFlats);

    showFlatSuggestions();
}

/**
 * Show flat number suggestions.
 */
function showFlatSuggestions() {
    const $suggestionsContainer = $('#flat-suggestions');
    console.log('showFlatSuggestions called, container:', $suggestionsContainer);
    console.log('filteredFlats.length:', filteredFlats.length);

    if ($suggestionsContainer.length === 0) {
        console.log('No suggestions container found');
        return;
    }

    if (filteredFlats.length === 0) {
        console.log('No filtered flats, hiding suggestions');
        hideFlatSuggestions();
        return;
    }

    // Clear previous suggestions
    $suggestionsContainer.empty();
    console.log('Cleared previous suggestions');

    // Add suggestions
    console.log('Adding suggestions for', filteredFlats.length, 'flats');
    filteredFlats.forEach((flat, index) => {
        const $suggestionItem = $('<div>')
            .addClass('suggestion-item')
            .css({
                'padding': '10px',
                'cursor': 'pointer',
                'border-bottom': '1px solid #eee'
            })
            .html(`
                <strong>${flat.flat_number}</strong> - ${flat.owner_name}<br>
                <small>${flat.email} | ${flat.phone}</small>
            `)
            .on('click', () => {
                console.log('Clicked on flat:', flat);
                selectFlat(flat);
            })
            .on('mouseenter', function() {
                $(this).css('background-color', '#f5f5f5');
            })
            .on('mouseleave', function() {
                $(this).css('background-color', 'white');
            });

        $suggestionsContainer.append($suggestionItem);
        console.log(`Added suggestion ${index + 1}: ${flat.flat_number}`);
    });

    $suggestionsContainer.show();
    console.log('Set suggestions container display to block');

}

/**
 * Hide flat number suggestions.
 */
function hideFlatSuggestions() {
    const $suggestionsContainer = $('#flat-suggestions');
    console.log('hideFlatSuggestions called, container:', $suggestionsContainer);
    if ($suggestionsContainer.length > 0) {
        $suggestionsContainer.hide();
        console.log('Set suggestions container display to none');
    }
}

/**
 * Select a flat and populate the form.
 */
function selectFlat(flat) {
    // Set the flat number
    $('#id_flat_number').val(flat.flat_number);

    // Set the resident ID (hidden field)
    $('#id_resident_id').val(flat.id);

    // Populate auto-filled fields
    populateResidentData(flat);

    // Hide suggestions
    hideFlatSuggestions();
}

/**
 * Populate resident data from selected flat.
 */
function populateResidentData(flat) {
    // Split owner name into first and last name
    const nameParts = flat.owner_name.split(' ');
    const firstName = nameParts[0] || '';
    const lastName = nameParts.slice(1).join(' ') || '';

    // Populate fields
    $('#id_first_name').val(firstName);
    $('#id_last_name').val(lastName);
    $('#id_email').val(flat.email);
    $('#id_phone_number').val(flat.phone);
    $('#id_block').val(flat.block);

    // Make auto-populated fields read-only
    $('#id_first_name').prop('readonly', true);
    $('#id_last_name').prop('readonly', true);
    $('#id_email').prop('readonly', true);
    $('#id_phone_number').prop('readonly', true);
    $('#id_block').prop('readonly', true);

    // Add visual indication that fields are auto-populated
    const autoPopulatedFields = [
        'id_first_name', 'id_last_name', 'id_email', 'id_phone_number', 'id_block'
    ];

    autoPopulatedFields.forEach(fieldId => {
        $(`#${fieldId}`).css({
            'background-color': '#f8f9fa'
        }).attr('title', 'This field was auto-populated from the flat owner data');
    });
}

/**
 * Clear auto-populated data.
 */
function clearAutoPopulatedData() {
    // Clear hidden resident ID
    $('#id_resident_id').val('');

    // Clear flat number
    $('#id_flat_number').val('');

    // Clear auto-populated fields
    $('#id_first_name').val('');
    $('#id_last_name').val('');
    $('#id_email').val('');
    $('#id_phone_number').val('');
    $('#id_block').val('');

    // Make fields editable again
    const autoPopulatedFields = [
        'id_first_name', 'id_last_name', 'id_email', 'id_phone_number', 'id_block'
    ];

    autoPopulatedFields.forEach(fieldId => {
        $(`#${fieldId}`).prop('readonly', false).css({
            'background-color': ''
        }).removeAttr('title');
    });
}

/**
 * Fetch resident data when flat number loses focus.
 * This is a fallback in case the user types a flat number manually.
 */
function fetchResidentData() {
    const flatNumber = $('#id_flat_number').val();
    const residentId = $('#id_resident_id').val();

    // If we already have a resident ID, don't fetch again
    if (residentId) return;

    if (!flatNumber) return;

    // Find matching flat in available flats
    const matchingFlat = availableFlats.find(flat =>
        flat.flat_number.toLowerCase() === flatNumber.toLowerCase()
    );

    if (matchingFlat) {
        selectFlat(matchingFlat);
    }
}


/**
 * Handle form submission validation.
 */
function validateForm() {
    const userType = $('#id_user_type').val();
    const residentType = $('#id_resident_type').val();
    const flatNumber = $('#id_flat_number').val();
    const residentId = $('#id_resident_id').val();

    // Validate owner residents have selected a flat
    if (userType === 'resident' && residentType === 'owner') {
        if (!flatNumber) {
            alert('Please select a flat number for owner residents.');
            return false;
        }

        if (!residentId) {
            alert('Please select a valid flat from the suggestions.');
            return false;
        }
    }

    return true;
}

// Add form validation to the form submission
$('form').on('submit', function(event) {
    if (!validateForm()) {
        event.preventDefault();
        return false;
    }
});