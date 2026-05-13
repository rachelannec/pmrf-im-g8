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
        const dependentRows = Array.from(dependentsContainer.querySelectorAll('.dependent-row'));

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