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
 * This fetches flats based on the current user type (owner vs tenant).
 */
function loadAvailableFlats() {
    // Determine the user type from the form
    const userType = $('#id_user_type').val();
    const residentType = $('#id_resident_type').val();

    // Set the API parameter based on resident type
    let apiUserType = 'owner'; // Default for backward compatibility

    if (userType === 'resident' && residentType === 'tenant') {
        apiUserType = 'tenant';
    } else if (userType === 'resident' && residentType === 'owner') {
        apiUserType = 'owner';
    }

    console.log('Loading available flats from API for user type:', apiUserType);
    fetch(`/backend/api/flats/available/?user_type=${apiUserType}`)
        .then(response => {
            console.log('API response status:', response.status);
            return response.json();
        })
        .then(data => {
            availableFlats = data.flats || [];
            console.log('Loaded available flats:', availableFlats.length, 'flats for', apiUserType, 'mode');
            console.log('Sample flats:', availableFlats.slice(0, 3));
        })
        .catch(error => {
            console.error('Error loading available flats:', error);
            // Fallback: create some sample data for testing
            availableFlats = [
                { id: 1, flat_number: 'A-101', block: 'A', owner_name: 'Meeraj Khalid', email: 'merajkhalidips@gmail.com', phone: '+919836293377', has_user: false },
                { id: 2, flat_number: 'A-102', block: 'A', owner_name: 'Ishani Paul', email: 'ishanipaul@gmail.com', phone: '+919989702225', has_user: true },
                { id: 3, flat_number: 'B-101', block: 'B', owner_name: 'Amit Javalgi', email: 'amitpjavalgi@gmail.com', phone: '+919547963285', has_user: false },
                { id: 4, flat_number: 'C1-201', block: 'C1', owner_name: 'Ajay Kumar Thakur', email: 'ajay956@gmail.com', phone: '+919051500356', has_user: true },
                { id: 5, flat_number: 'D-301', block: 'D', owner_name: 'Alok Rajoria', email: 'akrajoriaips@gmail.com', phone: '+919051217042', has_user: false },
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
 * Shows/hides owner-specific fields and sets up appropriate behavior.
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

        // Set up flat number autocomplete with auto-population
        console.log('Setting up autocomplete for owner');
        setupFlatNumberAutocomplete();

        // Reload flats data for owner mode (shows only available flats)
        loadAvailableFlats();

        // Remove tenant mode indicator if it exists
        $('.tenant-mode-indicator').remove();

    } else if (residentType === 'tenant') {
        console.log('Tenant selected, showing flat selection but allowing manual input');
        // Show owner-specific fields (flat selection)
        ownerFields.show();

        // Make flat number required for tenants (they need to select a flat)
        $('#id_flat_number').prop('required', true);

        // Set up flat number autocomplete but WITHOUT auto-population
        console.log('Setting up autocomplete for tenant (manual input mode)');
        setupFlatNumberAutocompleteForTenant();

        // Reload flats data for tenant mode (shows all flats, not just available ones)
        loadAvailableFlats();

    } else {
        // Family member or other - hide owner-specific fields
        console.log(' or other selected, hiding owner fields');
        ownerFields.hide();

        // Make flat number not required for family members
        $('#id_flat_number').prop('required', false);

        // Clear any populated data
        clearAutoPopulatedData();

        // Remove tenant mode indicator if it exists
        $('.tenant-mode-indicator').remove();
    }
}

/**
 * Set up autocomplete functionality for flat number input (for owners).
 * This version auto-populates personal fields when a flat is selected.
 */
function setupFlatNumberAutocomplete() {
    const $flatNumberInput = $('#id_flat_number');
    console.log('Setting up autocomplete for owner:', $flatNumberInput);

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
 * Set up autocomplete functionality for flat number input (for tenants).
 * This version shows flat suggestions but does NOT auto-populate personal fields.
 * Tenants can manually enter their own name, email, and phone details.
 */
function setupFlatNumberAutocompleteForTenant() {
    const $flatNumberInput = $('#id_flat_number');
    console.log('Setting up autocomplete for tenant (manual input mode):', $flatNumberInput);

    // Create suggestions container
    let $suggestionsContainer = $('#flat-suggestions');
    if ($suggestionsContainer.length === 0) {
        $suggestionsContainer = $('<div>')
            .attr('id', 'flat-suggestions')
            .addClass('flat-suggestions')
            .css({
                'position': 'absolute',
                'background': 'white',
                'border': '2px solid #0d6efd',
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
            console.log('Added suggestions container to parent for tenant');
        } else {
            console.log('Could not find parent container');
        }
    }

    // Clear any existing auto-populated data to ensure manual input
    clearAutoPopulatedData();

    // Add visual indicator for tenant mode
    addTenantModeIndicator();
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
                ${$('#id_resident_type').val() === 'tenant' ? 
                    `<br><em style="color: #666;">You will enter your own details below</em>` + 
                    (flat.has_user ? '<br><span style="color: #28a745; font-weight: bold;">✓ Flat has owner</span>' : '<br><span style="color: #ffc107; font-weight: bold;">⚠ Flat available</span>') 
                    : ''}
            `)
            .on('click', () => {
                console.log('Clicked on flat:', flat);
                // Use appropriate selection function based on resident type
                const residentType = $('#id_resident_type').val();
                if (residentType === 'tenant') {
                    selectFlatForTenant(flat);
                } else {
                    selectFlat(flat);
                }
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
 * Select a flat and populate the form (for owners).
 * This auto-populates all personal fields with owner data.
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
 * Select a flat for tenant (manual input mode).
 * This only sets the flat number and block, but leaves personal fields for manual input.
 * 
 * Note: For tenants, the resident_id points to the owner's resident record,
 * but we create a NEW tenant resident record with the same flat_number/block.
 */
function selectFlatForTenant(flat) {
    // Set the flat number
    $('#id_flat_number').val(flat.flat_number);

    // Set the resident ID (hidden field) - this references the owner's resident record
    // The backend will use this to get flat info but create a new tenant record
    $('#id_resident_id').val(flat.id);

    // Only populate block field (this is property-specific, not personal)
    $('#id_block').val(flat.block);

    // Make block field read-only since it's property-specific
    $('#id_block').prop('readonly', true).css({
        'background-color': '#f8f9fa'
    }).attr('title', 'Block is automatically set based on the selected flat');

    // Ensure personal fields are editable for tenant input
    const personalFields = ['id_first_name', 'id_last_name', 'id_email', 'id_phone_number'];
    personalFields.forEach(fieldId => {
        $(`#${fieldId}`).prop('readonly', false).css({
            'background-color': ''
        }).removeAttr('title');
    });

    console.log('Flat selected for tenant:', flat.flat_number, 'Block:', flat.block);
    console.log('Personal fields cleared for manual tenant input');

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
 * Add visual indicator for tenant mode to help users understand they need to enter their own details.
 */
function addTenantModeIndicator() {
    // Remove any existing tenant mode indicator
    $('.tenant-mode-indicator').remove();

    // Add indicator above the personal fields
    const personalFieldsContainer = $('#id_first_name').closest('.mb-3').parent();
    if (personalFieldsContainer.length > 0) {
        const $indicator = $('<div>')
            .addClass('tenant-mode-indicator alert alert-info')
            .css({
                'margin-bottom': '15px',
                'padding': '10px',
                'border-radius': '5px',
                'border': '1px solid #bee5eb',
                'background-color': '#d1ecf1',
                'color': '#0c5460'
            })
            .html(`
                <i class="fas fa-info-circle me-2"></i>
                <strong>Tenant Mode:</strong> You will enter your own personal details below. 
                The flat number and block will be automatically set when you select a flat above.
            `);

        // Insert before the first personal field
        personalFieldsContainer.prepend($indicator);
        console.log('Added tenant mode indicator');
    }
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
        // Use appropriate selection function based on resident type
        const residentType = $('#id_resident_type').val();
        if (residentType === 'tenant') {
            selectFlatForTenant(matchingFlat);
        } else {
            selectFlat(matchingFlat);
        }
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

    // Validate residents have selected a flat (both owners and tenants need to select a flat)
    if (userType === 'resident' && (residentType === 'owner' || residentType === 'tenant')) {
        if (!flatNumber) {
            const residentTypeText = residentType === 'owner' ? 'owner' : 'tenant';
            alert(`Please select a flat number for ${residentTypeText} residents.`);
            return false;
        }

        if (!residentId) {
            alert('Please select a valid flat from the suggestions.');
            return false;
        }
    }

    // Additional validation for tenants - ensure they've entered their personal details
    if (userType === 'resident' && residentType === 'tenant') {
        const firstName = $('#id_first_name').val().trim();
        const lastName = $('#id_last_name').val().trim();
        const email = $('#id_email').val().trim();
        const phone = $('#id_phone_number').val().trim();

        if (!firstName) {
            alert('Please enter your first name.');
            $('#id_first_name').focus();
            return false;
        }

        if (!lastName) {
            alert('Please enter your last name.');
            $('#id_last_name').focus();
            return false;
        }

        if (!email) {
            alert('Please enter your email address.');
            $('#id_email').focus();
            return false;
        }

        if (!phone) {
            alert('Please enter your phone number.');
            $('#id_phone_number').focus();
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