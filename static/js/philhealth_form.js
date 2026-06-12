window.addEventListener('error', function(e) {
    const messages = document.getElementById('messages') || document.getElementById('manage-message');
    if (messages) {
        messages.innerHTML = `
            <div class="alert alert-error" style="color: red; background: #fee; border: 1px solid #fda; padding: 10px; margin: 10px 0;">
                <strong>JS Error:</strong> ${e.message} at ${e.filename}:${e.lineno}:${e.colno}
            </div>
        `;
    }
});

const form = document.getElementById('phil-form');
const messages = document.getElementById('messages');
const permAddress = document.querySelector('textarea[name="PermanentAddress"]');
const mailAddress = document.getElementById('mailing_address');
const sameAddress = document.getElementById('same_address');
const dependentsContainer = document.getElementById('dependents-container');
const lastName = document.getElementById('last_name');
const firstName = document.getElementById('first_name');
const middleName = document.getElementById('middle_name');
const suffixInput = document.getElementById('suffix');
const memberNameInput = document.querySelector('input[name="MemberName"]');

const birthDateInput = document.getElementById('birth_date');

// Auto-capitalize name fields as the user types
document.addEventListener('input', (e) => {
    // List the IDs or Names of the fields we want to force to uppercase
    const uppercaseFields = ['last_name', 'first_name', 'middle_name', 'suffix', 'MotherMaidenName', 'SpouseName', 'DependentName'];
    
    if (uppercaseFields.includes(e.target.id) || uppercaseFields.includes(e.target.name)) {
        // Save the cursor position so it doesn't jump to the end of the word
        const start = e.target.selectionStart;
        const end = e.target.selectionEnd;
        
        // Force the text to uppercase
        e.target.value = e.target.value.toUpperCase();
        
        // Put the cursor back where it was
        e.target.setSelectionRange(start, end);
    }
});

// Calculate the maximum allowed date (21 years ago today)
const today = new Date();
const maxDate = new Date(today.getFullYear() - 21, today.getMonth(), today.getDate());
// Get exactly today's date in YYYY-MM-DD format
const currentToday = new Date().toISOString().split('T')[0];

// Create a function that finds every dependent birthdate box and restricts it
function restrictDependentDates() {
    const depDateInputs = document.querySelectorAll('input[name="DependentBirthDate"]');
    depDateInputs.forEach(input => {
        input.setAttribute('max', currentToday);
    });
}

// Run it immediately when the page loads for the first row
restrictDependentDates();
// Format it to YYYY-MM-DD for the HTML input
const formattedMaxDate = maxDate.toISOString().split('T')[0];

const philsysInput = document.getElementById('philsys_id');

// Auto-format PhilSys ID as XXXX-XXXX-XXXX-XXXX
if (philsysInput) {
    bindFormatter('#philsys_id', formatPhilsysId);
}

const tinInput = document.getElementById('tin_id');

// Auto-format TIN as XXX-XXX-XXX or XXX-XXX-XXX-XXX
if (tinInput) {
    bindFormatter('#tin_id', formatTin);
}

const mobileInput = document.getElementById('mobile_phone');
const homeInput = document.getElementById('home_phone');
const sameAsMobileCheckbox = document.getElementById('same_as_mobile');

// Auto-format Mobile & Home Numbers
if (mobileInput) {
    bindFormatter('#mobile_phone, #home_phone', formatMobileNumber);
    mobileInput.addEventListener('input', function () {
        if (sameAsMobileCheckbox && sameAsMobileCheckbox.checked) {
            homeInput.value = this.value;
        }
    });
}

const businessInput = document.getElementById('business_line');

// Auto-format Business Line
if (businessInput) {
    bindFormatter('#business_line', formatBusinessLine);
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

const reviewModal = document.getElementById('review_modal');
const btnEdit = document.getElementById('btn_edit');
const btnConfirm = document.getElementById('btn_confirm');
const reviewDataContainer = document.getElementById('review_data_container');
// We will store the validated form data here so the confirm button can access it
let pendingFormData = null;

const steps = document.querySelectorAll('.step'); // Grabs the 3 progress steps

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
    // Produce format: XX-XXXXXXXXX-X (2-9-1)
    const left = Math.floor(Math.random() * 100).toString().padStart(2, '0');
    const middle = Math.floor(Math.random() * 1_000_000_000).toString().padStart(9, '0');
    const right = Math.floor(Math.random() * 10).toString();
    return `${left}-${middle}-${right}`;
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
    const suffix = suffixInput ? suffixInput.value.trim() : '';
    // Format: Lastname, Firstname suffix Middlename
    let nameParts = [];
    if (last) {
        let rest = first ? `${first}` : '';
        if (suffix) rest = rest ? `${rest} ${suffix}` : `${suffix}`;
        if (middle) rest = rest ? `${rest} ${middle}` : `${middle}`;
        memberNameInput.value = rest ? `${last}, ${rest}` : `${last}`;
    } else {
        memberNameInput.value = [first, suffix, middle].filter(Boolean).join(' ');
    }
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
        <td><input type="text" name="DependentName" class="table-input" placeholder="Last, First, MI" required></td>
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

const addDependentBtn = document.getElementById('add-dependent');

if (addDependentBtn) {
    addDependentBtn.addEventListener('click', () => {
        // 1. Create the new row
        dependentsContainer.appendChild(createDependentRow());
        
        // 2. Immediately restrict the calendar dates for that new row
        restrictDependentDates(); 
    });
}

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

// 1. Intercept the Submit Button to show the Review Modal
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMessage();

    // 1. Validate Member's own age (must be >= 21)
    if (birthDateInput && birthDateInput.value) {
        const memberAge = calculateAge(birthDateInput.value);
        if (memberAge === null || memberAge < 21) {
            showMessage('error', 'Member must be at least 21 years old.');
            birthDateInput.focus();
            return;
        }
    }

    // 2. Validate input formats (Mobile, Philsys, TIN, Business Line)
    if (!validateFormInputs(form)) {
        return;
    }

    // 3. Validate Dependent rows (Child must be < 21)
    const dependentRows = Array.from(dependentsContainer.querySelectorAll('.dependent-row'));
    for (const row of dependentRows) {
        if (!validateChildAge(row)) {
            return;
        }
    }

    updateMemberName();
    updateMailingAddress();

    pendingFormData = new FormData(form);
    
    // Auto-generate PIN if empty
    const pinInput = form.querySelector('input[name="PIN"]');
    if (!pinInput.value.trim()) {
        pendingFormData.set('PIN', generatePin());
    }

    if (!pendingFormData.get('MailingAddress')) {
        pendingFormData.set('MailingAddress', permAddress.value.trim());
    }

    // Generate the HTML for the Review Modal dynamically
    let summaryHTML = '';
    for (let [key, value] of pendingFormData.entries()) {
        // Skip empty fields and exclude the Suffix (already in MemberName)
        if (!value || key === 'Suffix') continue;

        // Friendly label: keep 'PIN' uppercase, otherwise split camelCase
        let readableKey = key === 'PIN' ? 'PIN' : key.replace(/([A-Z])/g, ' $1').trim();
        const displayValue = key === 'MemberPassword' ? '••••••••' : value;
        summaryHTML += `<div class="review-item"><strong>${readableKey}:</strong> ${displayValue}</div>`;
    }
    
    reviewDataContainer.innerHTML = summaryHTML;
    
    // Show Modal and update visual progress bar (Optional step)
    reviewModal.classList.add('show');
    
    // --- ADD THIS: Update Progress Bar to "Review" ---
    if (steps.length > 1) {
        steps[0].classList.remove('active');
        steps[1].classList.add('active');
    }
    
});

// Hide Modal if they click "Go Back & Edit"
btnEdit.addEventListener('click', () => {
    reviewModal.classList.remove('show');
    
    // --- ADD THIS: Revert Progress Bar back to "Form Entry" ---
    if (steps.length > 1) {
        steps[1].classList.remove('active');
        steps[0].classList.add('active');
    }
    // ----------------------------------------------------------
});

// 3. Save to Database if they click "Confirm & Submit"
btnConfirm.addEventListener('click', async () => {
    // Hide modal and show loading state if you want
    reviewModal.classList.remove('show');
    
    try {
        const registrant = await postForm('/registrants', pendingFormData);
        const savedPin = registrant.PIN || pendingFormData.get('PIN');
        const dependentRows = Array.from(dependentsContainer.querySelectorAll('.dependent-row'));

        for (const row of dependentRows) {
            const rel = row.querySelector('select[name="Relationship"]').value;
            const name = row.querySelector('input[name="DependentName"]').value.trim();
            if (rel && name) { // Only save if they actually filled it out
                const dependentData = new FormData();
                dependentData.set('PIN', savedPin);
                dependentData.set('DependentName', name);
                dependentData.set('Relationship', rel);
                dependentData.set('DependentBirthDate', row.querySelector('input[name="DependentBirthDate"]').value);
                dependentData.set('DependentCitizenship', row.querySelector('select[name="DependentCitizenship"]').value);
                dependentData.set('DependentPWD', row.querySelector('select[name="DependentPWD"]').value);

                await postForm('/dependents', dependentData);
            }
        }

        showMessage('success', `Registration saved successfully! PIN: ${savedPin}`);
        form.reset();
        dependentsContainer.innerHTML = '';
        dependentsContainer.appendChild(createDependentRow());
        dependentsContainer.appendChild(createDependentRow());
        restrictDependentDates();
        
        // Update visual progress bar to "Complete" here!
        if (steps.length > 2) {
            steps[1].classList.remove('active');
            steps[2].classList.add('active');
        }

        // 2. Hide the original form and headers so the screen is blank
        form.style.display = 'none';
        document.querySelector('.form-header').style.display = 'none';
        document.getElementById('messages').style.display = 'none';

        // 3. Copy the summary text from the Review modal directly into the Complete screen
        document.getElementById('final_summary_container').innerHTML = reviewDataContainer.innerHTML;

        // 4. Show the new Complete Screen
        document.getElementById('complete-view').style.display = 'block';
        
        // 5. Scroll to the top of the page so they see the big green checkmark
        window.scrollTo({ top: 0, behavior: 'smooth' });

    } catch (error) {
        showMessage('error', error.message || 'Registration failed.');
    }
});

if (!dependentsContainer.children.length) {
    dependentsContainer.appendChild(createDependentRow());
}
restrictDependentDates();
loadMemberTypes();

// Reset everything to start a new registration
document.getElementById('btn_register_another').addEventListener('click', () => {
    // Reset the form data
    form.reset();
    dependentsContainer.innerHTML = '';
    dependentsContainer.appendChild(createDependentRow());
    restrictDependentDates();
    
    // Swap the screens back
    document.getElementById('complete-view').style.display = 'none';
    form.style.display = 'block';
    document.querySelector('.form-header').style.display = 'block';
    document.getElementById('messages').style.display = 'block';
    
    // Reset the progress bar back to Step 1
    if (steps.length > 2) {
        steps[2].classList.remove('active');
        steps[0].classList.add('active');
    }
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
});