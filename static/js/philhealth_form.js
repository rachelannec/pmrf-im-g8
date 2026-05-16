const form = document.getElementById('phil-form');
const messages = document.getElementById('messages');
const permAddress = document.querySelector('textarea[name="PermanentAddress"]');
const mailAddress = document.getElementById('mailing_address');
const sameAddress = document.getElementById('same_address');
const dependentsContainer = document.getElementById('dependents-container');
const lastName = document.getElementById('last_name');
const firstName = document.getElementById('first_name');
const middleName = document.getElementById('middle_name');
const memberNameInput = document.querySelector('input[name="MemberName"]');

const birthDateInput = document.getElementById('birth_date');

// Calculate the maximum allowed date (21 years ago today)
const today = new Date();
const maxDate = new Date(today.getFullYear() - 21, today.getMonth(), today.getDate());
// Format it to YYYY-MM-DD for the HTML input
const formattedMaxDate = maxDate.toISOString().split('T')[0];

const philsysInput = document.getElementById('philsys_id');


// Auto-format PhilSys ID as XXXX-XXXX-XXXX-XXXX
if (philsysInput) {
    philsysInput.addEventListener('input', function (e) {
        // 1. Strip out anything that isn't a number
        let rawValue = this.value.replace(/\D/g, '');
        
        // 2. Limit to exactly 16 digits
        if (rawValue.length > 16) {
            rawValue = rawValue.substring(0, 16);
        }
        
        // 3. Add a hyphen after every 4th digit
        let formattedValue = '';
        for (let i = 0; i < rawValue.length; i++) {
            if (i > 0 && i % 4 === 0) {
                formattedValue += '-';
            }
            formattedValue += rawValue[i];
        }
        
        // 4. Update the input box
        this.value = formattedValue;
    });
}

const tinInput = document.getElementById('tin_id');

// Auto-format TIN as XXX-XXX-XXX or XXX-XXX-XXX-XXX
if (tinInput) {
    tinInput.addEventListener('input', function (e) {
        // 1. Strip out anything that isn't a number
        let rawValue = this.value.replace(/\D/g, '');
        
        // 2. Limit to exactly 12 digits max
        if (rawValue.length > 12) {
            rawValue = rawValue.substring(0, 12);
        }
        
        // 3. Add a hyphen after every 3rd digit
        let formattedValue = '';
        for (let i = 0; i < rawValue.length; i++) {
            if (i > 0 && i % 3 === 0) {
                formattedValue += '-';
            }
            formattedValue += rawValue[i];
        }
        
        // 4. Update the input box
        this.value = formattedValue;
    });
}

const mobileInput = document.getElementById('mobile_phone');
const homeInput = document.getElementById('home_phone');
const sameAsMobileCheckbox = document.getElementById('same_as_mobile');

// Auto-format Mobile Number
if (mobileInput) {
    mobileInput.addEventListener('input', function () {
        // 1. Strip out anything that isn't a number
        let numbers = this.value.replace(/\D/g, '');
        
        // 2. Remove leading 63 or 0 so we just deal with the 10-digit number
        if (numbers.startsWith('63')) numbers = numbers.substring(2);
        if (numbers.startsWith('0')) numbers = numbers.substring(1);
        
        // 3. Limit to 10 digits total
        if (numbers.length > 10) {
            numbers = numbers.substring(0, 10);
        }
        
        // 4. Build the +63-9XX-XXX-XXXX format
        let formattedValue = '';
        if (numbers.length > 0) {
            formattedValue = '+63';
            if (numbers.length > 0) formattedValue += '-' + numbers.substring(0, 3);
            if (numbers.length > 3) formattedValue += '-' + numbers.substring(3, 6);
            if (numbers.length > 6) formattedValue += '-' + numbers.substring(6, 10);
        }
        
        this.value = formattedValue;

        // 5. If "Same as mobile" is checked, sync the home phone instantly
        if (sameAsMobileCheckbox && sameAsMobileCheckbox.checked) {
            homeInput.value = this.value;
        }
    });
}

// "Same as mobile number" checkbox logic
if (sameAsMobileCheckbox) {
    sameAsMobileCheckbox.addEventListener('change', function () {
        if (this.checked) {
            homeInput.value = mobileInput.value;
            homeInput.setAttribute('readonly', 'readonly');
        } else {
            homeInput.removeAttribute('readonly');
        }
    });
}

// Apply the restriction to the calendar picker
if (birthDateInput) {
    birthDateInput.setAttribute('max', formattedMaxDate);
}

function showMessage(type, text) {
    const icon = type === 'error' ? 'error' : 'check_circle';
    messages.innerHTML = `
        <div class="alert alert-${type}">
            <span class="material-symbols-outlined">${icon}</span> ${text}
        </div>
    `;
    messages.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function clearMessage() {
    messages.innerHTML = '';
}

function generatePin() {
    return `PH-${Math.floor(Math.random() * 1_000_000_000).toString().padStart(9, '0')}-${Math.floor(Math.random() * 10)}`;
}

function updateMailingAddress() {
    if (sameAddress.checked) {
        mailAddress.value = permAddress.value;
        mailAddress.setAttribute('readonly', 'readonly');
    } else {
        mailAddress.removeAttribute('readonly');
    }
}

function updateMemberName() {
    const last = lastName.value.trim();
    const first = firstName.value.trim();
    const middle = middleName.value.trim();
    memberNameInput.value = [last, first, middle].filter(Boolean).length
        ? `${last}, ${first}${middle ? ` ${middle}` : ''}`
        : '';
}

lastName.addEventListener('input', updateMemberName);
firstName.addEventListener('input', updateMemberName);
middleName.addEventListener('input', updateMemberName);
permAddress.addEventListener('input', updateMailingAddress);
sameAddress.addEventListener('change', updateMailingAddress);

function createDependentRow() {
    const tr = document.createElement('tr');
    tr.className = 'dependent-row';
    tr.innerHTML = `
        <td><input type="text" name="DependentName" class="table-input" placeholder="Full legal name" required></td>
        <td>
            <select name="Relationship" class="table-input" required>
                <option value="" disabled selected>Select...</option>
                <option value="Spouse">Spouse</option>
                <option value="Child">Child</option>
                <option value="Parent">Parent</option>
            </select>
        </td>
        <td><input type="date" name="DependentBirthDate" class="table-input" required></td>
        <td>
            <select name="DependentCitizenship" class="table-input" required>
                <option value="Filipino" selected>Filipino</option>
                <option value="Foreign National">Foreign National</option>
                <option value="Dual Citizen">Dual Citizen</option>
            </select>
        </td>
        <td>
            <select name="DependentPWD" class="table-input" required>
                <option value="No" selected>No</option>
                <option value="Yes">Yes</option>
            </select>
        </td>
        <td style="text-align: center;">
            <button type="button" class="btn-icon"><span class="material-symbols-outlined">delete</span></button>
        </td>
    `;
    tr.querySelector('.btn-icon').addEventListener('click', () => tr.remove());
    return tr;
}

function calculateAge(birthDateString) {
    const today = new Date();
    const birthDate = new Date(birthDateString);
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    // Subtract 1 year if their birthday hasn't happened yet this year
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    return age;
}

document.getElementById('add-dependent').addEventListener('click', () => {
    dependentsContainer.appendChild(createDependentRow());
});

function createMemberTypeOption(mt) {
    const label = document.createElement('label');
    label.className = 'member-option';
    label.innerHTML = `
        <input type="radio" name="MemberTypeID" value="${mt.MemberTypeID}" required>
        <div>
            <span class="member-title">${mt.MemberType}</span>
            <span class="member-desc">ID: ${mt.MemberTypeID}</span>
        </div>
    `;
    return label;
}

async function loadMemberTypes() {
    try {
        const res = await fetch('/membertypes');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const directContainer = document.getElementById('direct-contributors');
        const indirectContainer = document.getElementById('indirect-contributors');
        const memberList = Array.isArray(data) ? data : (data.membertypes || []);

        if (!memberList.length) {
            showMessage('error', 'No member types found. Please seed the database lookup table.');
            return;
        }

        memberList.forEach((mt) => {
            if (['EMP', 'GOV', 'SLF', 'OFW'].includes(mt.MemberTypeID) || (mt.MemberTypeID || '').toUpperCase().startsWith('D')) {
                directContainer.appendChild(createMemberTypeOption(mt));
            } else {
                indirectContainer.appendChild(createMemberTypeOption(mt));
            }
        });
    } catch (e) {
        console.error(e);
        showMessage('error', 'Failed to load Member Types from the API.');
    }
}

function serializeFormData(formData) {
    return new URLSearchParams(formData).toString();
}

async function postForm(url, formData) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
        body: serializeFormData(formData),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.message || `HTTP ${response.status}`);
    return payload;
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMessage();

    // --- PRIMARY MEMBER AGE VALIDATION ---
    const userBirthDate = new Date(birthDateInput.value);
    if (userBirthDate > maxDate) {
        showMessage('error', 'You must be at least 21 years old to register as a primary member.');
        return; 
    }

    // --- PHILSYS ID VALIDATION ---
    if (philsysInput.value) {
        // Count just the numbers, ignoring the hyphens
        const digitCount = philsysInput.value.replace(/\D/g, '').length;
        if (digitCount !== 16) {
            showMessage('error', 'PhilSys ID must be exactly 16 digits.');
            return; // Stops the submission
        }
    }

    // --- TIN VALIDATION ---
    if (tinInput && tinInput.value) {
        // Count just the numbers, ignoring the hyphens
        const digitCount = tinInput.value.replace(/\D/g, '').length;
        if (digitCount < 9 || digitCount > 12) {
            showMessage('error', 'TIN must be between 9 and 12 digits.');
            return; // Stops the submission
        }
    }

    // --- MOBILE NUMBER VALIDATION ---
    if (mobileInput && mobileInput.value) {
        if (mobileInput.value.length !== 16) {
            showMessage('error', 'Please enter a complete 10-digit mobile number.');
            return; // Stops the submission
        }
    }
    

    // --- DEPENDENT VALIDATION ---
    const dependentRows = Array.from(dependentsContainer.querySelectorAll('.dependent-row'));
    
    for (const row of dependentRows) {
        const relationship = row.querySelector('select[name="Relationship"]').value;
        const birthDateVal = row.querySelector('input[name="DependentBirthDate"]').value;
        const pwdStatus = row.querySelector('select[name="DependentPWD"]').value;

        // Only validate if they actually filled out the row
        if (relationship && birthDateVal) {
            const age = calculateAge(birthDateVal);

            if (relationship === 'Child') {
                if (age >= 21 && pwdStatus === 'No') {
                    showMessage('error', 'A child dependent must be below 21 years old unless they have a permanent disability (PWD).');
                    return; // Stops the submission
                }
            }

            if (relationship === 'Parent') {
                if (age < 60 && pwdStatus === 'No') {
                    showMessage('error', 'A parent dependent must be 60 years old or above unless they have a permanent disability (PWD).');
                    return; // Stops the submission
                }
            }
        }
    }
    // ----------------------------

    updateMemberName();
    updateMailingAddress();

    const formData = new FormData(form);
    const pinInput = form.querySelector('input[name="PIN"]');

    if (!pinInput.value.trim()) {
        pinInput.value = generatePin();
        formData.set('PIN', pinInput.value);
    }

    if (!formData.get('MailingAddress')) {
        formData.set('MailingAddress', permAddress.value.trim());
    }

    try {
        const registrant = await postForm('/registrants', formData);
        const savedPin = registrant.PIN || formData.get('PIN');

        for (const row of dependentRows) {
            const dependentData = new FormData();
            dependentData.set('PIN', savedPin);
            dependentData.set('DependentName', row.querySelector('input[name="DependentName"]').value.trim());
            dependentData.set('Relationship', row.querySelector('select[name="Relationship"]').value);
            dependentData.set('DependentBirthDate', row.querySelector('input[name="DependentBirthDate"]').value);
            dependentData.set('DependentCitizenship', row.querySelector('select[name="DependentCitizenship"]').value);
            dependentData.set('DependentPWD', row.querySelector('select[name="DependentPWD"]').value);

            await postForm('/dependents', dependentData);
        }

        showMessage('success', `Registration saved successfully! PIN: ${savedPin}`);
        form.reset();
        dependentsContainer.innerHTML = '';
        dependentsContainer.appendChild(createDependentRow());
        updateMailingAddress();
    } catch (error) {
        showMessage('error', error.message || 'Registration failed.');
    }
});

if (!dependentsContainer.children.length) dependentsContainer.appendChild(createDependentRow());
loadMemberTypes();