/* Project specific Javascript goes here. */
$(document).ready(function() {

    // Enhanced signup form functionality - only run on signup page
    if (window.location.pathname.includes('/accounts/signup/') || $('#id_user_type').length > 0) {

        console.log('=== SIGNUP FORM DEBUG ===');
        console.log('Found resident fields by class:', $('.resident-field').length);
        console.log('User type field:', $('#id_user_type').length);
        console.log('Resident type field:', $('#id_resident_type').length);
        console.log('Flat number field:', $('#id_flat_number').length);
        console.log('Block field:', $('#id_block').length);
        console.log('Move in date field:', $('#id_move_in_date').length);

        // List all form fields to see what's actually rendered
        console.log('All form fields:');
        $('form input, form select').each(function() {
            console.log('- Field:', this.id, 'Type:', this.type, 'Name:', this.name);
        });
        console.log('=== END DEBUG ===');

        // Add styling
        $('<style>').prop('type', 'text/css').html(`
            .resident-field-group { 
                transition: all 0.3s ease-in-out; 
                display: none !important; 
            }
            .resident-field-group.show { 
                display: block !important; 
            }
            #id_user_type {
                font-weight: 500;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border: 2px solid #dee2e6;
                border-radius: 8px;
            }
            #id_user_type:focus {
                border-color: #0d6efd;
                box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
            }
            .resident-field { border-left: 3px solid #0d6efd; }
        `).appendTo('head');

        // Hide resident fields initially
        $('.resident-field').each(function() {
            $(this).closest('.form-group, .mb-3, .field').addClass('resident-field-group').hide();
        });

        // Also hide by IDs (fallback)
        $('#id_resident_type, #id_flat_number, #id_block, #id_move_in_date').each(function() {
            $(this).closest('.form-group, .mb-3, .field').addClass('resident-field-group').hide();
        });

        // Handle user type changes - using direct inline approach
        function handleUserTypeChange() {
            console.log('handleUserTypeChange called');

            var userType = $('#id_user_type').val();
            console.log('Current user type:', userType);

            var $residentFields = $('.resident-field-group');
            console.log('Found resident field groups:', $residentFields.length);

            // Debug: Log each field group
            $residentFields.each(function(index) {
                console.log('Field group', index, ':', this);
                console.log('  - Contains field:', $(this).find('input, select').attr('id'));
                console.log('  - Is visible:', $(this).is(':visible'));
                console.log('  - Display style:', $(this).css('display'));
            });

            if (userType === 'resident') {
                console.log('Showing resident fields');
                $residentFields.addClass('show').removeClass('hide');
                $('#id_resident_type, #id_flat_number').prop('required', true);

                // Add required indicators
                $('#id_resident_type').closest('.form-group, .mb-3, .field').find('label').each(function() {
                    if (!$(this).find('.text-danger').length) {
                        $(this).append(' <span class="text-danger">*</span>');
                    }
                });
                $('#id_flat_number').closest('.form-group, .mb-3, .field').find('label').each(function() {
                    if (!$(this).find('.text-danger').length) {
                        $(this).append(' <span class="text-danger">*</span>');
                    }
                });

            } else {
                console.log('Hiding resident fields');
                $residentFields.removeClass('show').addClass('hide');
                $('#id_resident_type, #id_flat_number, #id_block, #id_move_in_date').prop('required', false).val('');

                // Remove required indicators
                $('.resident-field-group label .text-danger').remove();
            }
        }

        // Initialize on page load
        setTimeout(function() {
            console.log('Initializing form...');
            handleUserTypeChange();
        }, 300);

        // Handle changes
        $('#id_user_type').on('change', function() {
            console.log('User type changed to:', $(this).val());
            handleUserTypeChange();
        });

        // Form validation
        $('form').on('submit', function(event) {
            var userType = $('#id_user_type').val();
            var residentType = $('#id_resident_type').val();
            var flatNumber = $('#id_flat_number').val();

            console.log('Form submitted - User type:', userType, 'Resident type:', residentType, 'Flat number:', flatNumber);

            if (userType === 'resident') {
                if (!residentType) {
                    event.preventDefault();
                    alert('Please select your resident type.');
                    $('#id_resident_type').focus();
                    return false;
                }

                if (!flatNumber) {
                    event.preventDefault();
                    alert('Please enter your flat number.');
                    $('#id_flat_number').focus();
                    return false;
                }
            }

            return true;
        });
    }

});