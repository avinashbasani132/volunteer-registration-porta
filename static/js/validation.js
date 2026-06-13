document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registrationForm');
    if (!form) return;

    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');
    const availabilitySelect = document.getElementById('availability');
    const skillsCheckboxes = document.querySelectorAll('input[name="skills"]');
    
    const nameFeedback = document.getElementById('nameFeedback');
    const emailFeedback = document.getElementById('emailFeedback');
    const phoneFeedback = document.getElementById('phoneFeedback');
    const skillsFeedback = document.getElementById('skillsFeedback');
    const availabilityFeedback = document.getElementById('availabilityFeedback');
    
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const btnSpinner = document.getElementById('btnSpinner');

    // Email Regex Pattern
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

    // Phone Number Regex Pattern (10-15 digits, digits only)
    const phoneRegex = /^[0-9]{10,15}$/;

    // Helper functions for displaying validity states
    function setValid(input, feedback) {
        input.classList.remove('is-invalid-custom');
        input.classList.add('is-valid-custom');
        if (feedback) feedback.classList.add('d-none');
        return true;
    }

    function setInvalid(input, feedback) {
        input.classList.remove('is-valid-custom');
        input.classList.add('is-invalid-custom');
        if (feedback) feedback.classList.remove('d-none');
        return false;
    }

    // Individual validators
    function validateName() {
        const value = nameInput.value.trim();
        if (value.length >= 2) {
            return setValid(nameInput, nameFeedback);
        } else {
            return setInvalid(nameInput, nameFeedback);
        }
    }

    function validateEmail() {
        const value = emailInput.value.trim();
        if (emailRegex.test(value)) {
            return setValid(emailInput, emailFeedback);
        } else {
            return setInvalid(emailInput, emailFeedback);
        }
    }

    function validatePhone() {
        const value = phoneInput.value.trim();
        // Remove non-numeric characters for check to assist user
        const cleanVal = value.replace(/\D/g, '');
        if (cleanVal !== value) {
            phoneInput.value = cleanVal;
        }
        if (phoneRegex.test(cleanVal)) {
            return setValid(phoneInput, phoneFeedback);
        } else {
            return setInvalid(phoneInput, phoneFeedback);
        }
    }

    function validateSkills() {
        let checkedCount = 0;
        skillsCheckboxes.forEach(cb => {
            if (cb.checked) checkedCount++;
        });
        
        if (checkedCount > 0) {
            skillsFeedback.classList.add('d-none');
            return true;
        } else {
            skillsFeedback.classList.remove('d-none');
            return false;
        }
    }

    function validateAvailability() {
        const value = availabilitySelect.value;
        if (value && value !== "") {
            return setValid(availabilitySelect, availabilityFeedback);
        } else {
            return setInvalid(availabilitySelect, availabilityFeedback);
        }
    }

    // Attach real-time input event listeners
    nameInput.addEventListener('input', validateName);
    emailInput.addEventListener('input', validateEmail);
    phoneInput.addEventListener('input', validatePhone);
    phoneInput.addEventListener('keypress', function(e) {
        // Prevent typing non-numeric characters
        if (e.key < '0' || e.key > '9') {
            e.preventDefault();
        }
    });
    availabilitySelect.addEventListener('change', validateAvailability);
    skillsCheckboxes.forEach(cb => {
        cb.addEventListener('change', validateSkills);
    });

    // Handle Form Submission
    form.addEventListener('submit', function(e) {
        // Run all validations
        const isNameValid = validateName();
        const isEmailValid = validateEmail();
        const isPhoneValid = validatePhone();
        const isSkillsValid = validateSkills();
        const isAvailabilityValid = validateAvailability();

        const isFormValid = isNameValid && isEmailValid && isPhoneValid && isSkillsValid && isAvailabilityValid;

        if (!isFormValid) {
            e.preventDefault();
            // Scroll to the first error element if possible
            const firstInvalid = form.querySelector('.is-invalid-custom, .form-check-input:invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        } else {
            // Form is valid - display submit loading state
            submitBtn.disabled = true;
            btnText.textContent = "Submitting...";
            btnSpinner.classList.remove('d-none');
        }
    });
});
