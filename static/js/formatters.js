// Shared Input Formatter Utilities

function formatMobileNumber(value) {
    let numbers = String(value || '').replace(/\D/g, '');

    if (numbers.startsWith('63')) {
        numbers = numbers.slice(2);
    }
    if (numbers.startsWith('0')) {
        numbers = numbers.slice(1);
    }

    numbers = numbers.slice(0, 10);
    if (!numbers) {
        return '';
    }

    let formatted = '+63';
    if (numbers.length > 0) formatted += `-${numbers.slice(0, 3)}`;
    if (numbers.length > 3) formatted += `-${numbers.slice(3, 6)}`;
    if (numbers.length > 6) formatted += `-${numbers.slice(6, 10)}`;

    return formatted;
}

function formatPhilsysId(value) {
    let digits = String(value || '').replace(/\D/g, '').slice(0, 16);
    let formatted = '';

    for (let index = 0; index < digits.length; index += 1) {
        if (index > 0 && index % 4 === 0) {
            formatted += '-';
        }
        formatted += digits[index];
    }

    return formatted;
}

function formatTin(value) {
    let digits = String(value || '').replace(/\D/g, '').slice(0, 12);
    let formatted = '';

    for (let index = 0; index < digits.length; index += 1) {
        if (index > 0 && index % 3 === 0) {
            formatted += '-';
        }
        formatted += digits[index];
    }

    return formatted;
}

function formatBusinessLine(value) {
    let digits = String(value || '').replace(/\D/g, '');
    
    // Determine area code length and max digits
    // (02) XXXX-XXXX for metro manila
    // (0XX) XXX-XXXX for other provinces
    let areaCodeLen = 2;
    if (digits.startsWith('02')) {
        areaCodeLen = 2;
    } else if (digits.startsWith('2')) {
        areaCodeLen = 1;
    } else if (digits.startsWith('0')) {
        areaCodeLen = 3;
    } else {
        areaCodeLen = 2;
    }
    
    let isAreaCode2 = (digits.startsWith('02') || digits.startsWith('2'));
    let subscriberLen = isAreaCode2 ? 8 : 7;
    let maxLen = areaCodeLen + subscriberLen;
    
    digits = digits.slice(0, maxLen);
    
    if (digits.length === 0) {
        return '';
    }
    
    let formatted = '(';
    if (digits.length <= areaCodeLen) {
        formatted += digits;
    } else {
        formatted += digits.slice(0, areaCodeLen) + ') ';
        let sub = digits.slice(areaCodeLen);
        let firstPartLen = isAreaCode2 ? 4 : 3;
        if (sub.length <= firstPartLen) {
            formatted += sub;
        } else {
            formatted += sub.slice(0, firstPartLen) + '-' + sub.slice(firstPartLen);
        }
    }
    return formatted;
}

function bindFormatter(selector, formatter) {
    document.querySelectorAll(selector).forEach(input => {
        input.value = formatter(input.value);
        input.addEventListener('input', () => {
            input.value = formatter(input.value);
        });
    });
}

function bindUppercase(selector) {
    document.querySelectorAll(selector).forEach(input => {
        input.value = String(input.value || '').toUpperCase();
        input.addEventListener('input', (e) => {
            const start = e.target.selectionStart;
            const end = e.target.selectionEnd;
            e.target.value = e.target.value.toUpperCase();
            e.target.setSelectionRange(start, end);
        });
    });
}

function calculateAge(birthDateString) {
    if (!birthDateString) {
        return null;
    }

    const today = new Date();
    const birthDate = new Date(birthDateString);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDelta = today.getMonth() - birthDate.getMonth();

    if (monthDelta < 0 || (monthDelta === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }

    return age;
}

function validateChildAge(form) {
    console.log("validateChildAge called on:", form);
    const relationshipInput = form.querySelector('input[name="Relationship"]');
    const relationshipSelect = form.querySelector('select[name="Relationship"]');
    const birthDateInput = form.querySelector('input[name="DependentBirthDate"]');

    console.log("Inputs found:", { relationshipInput, relationshipSelect, birthDateInput });

    if (!relationshipInput && !relationshipSelect) {
        return true;
    }
    if (!birthDateInput) {
        return true;
    }

    const relationshipValue = (relationshipSelect ? relationshipSelect.value : (relationshipInput ? relationshipInput.value : '')) || '';
    console.log("Relationship value:", relationshipValue);

    if (relationshipValue.trim().toLowerCase() !== 'child') {
        return true;
    }

    const age = calculateAge(birthDateInput.value);
    console.log("Calculated child age:", age);
    if (age === null || age >= 21) {
        alert('Child dependents must be below 21 years old.');
        birthDateInput.focus();
        return false;
    }

    return true;
}

function validateFormInputs(form) {
    console.log("validateFormInputs called on:", form);
    // 1. Mobile Number validation
    const mobileInput = form.querySelector('input[name="MobilePhone"]');
    if (mobileInput && mobileInput.value) {
        const val = mobileInput.value;
        console.log("Mobile val:", val);
        if (val.length < 16) {
            alert('Mobile number must be a valid 10-digit number (+63-9XX-XXX-XXXX).');
            mobileInput.focus();
            return false;
        }
    }

    // 2. PhilSys ID validation
    const philsysInput = form.querySelector('input[name="PhilSysID"]');
    if (philsysInput && philsysInput.value) {
        const val = philsysInput.value;
        console.log("PhilSys val:", val);
        if (val.length < 19) {
            alert('PhilSys ID must be exactly 16 digits.');
            philsysInput.focus();
            return false;
        }
    }

    // 3. TIN validation
    const tinInput = form.querySelector('input[name="TIN"]');
    if (tinInput && tinInput.value) {
        const val = tinInput.value;
        console.log("TIN val:", val);
        if (val.length !== 11 && val.length !== 15) {
            alert('TIN must be 9 or 12 digits (XXX-XXX-XXX or XXX-XXX-XXX-XXX).');
            tinInput.focus();
            return false;
        }
    }

    // 4. Business Line validation
    const businessInput = form.querySelector('input[name="BusinessLine"]');
    if (businessInput && businessInput.value) {
        const val = businessInput.value;
        console.log("Business Line val:", val);
        if (val.length < 14) {
            alert('Business line must be a valid landline number, e.g., (02) 8123-4567.');
            businessInput.focus();
            return false;
        }
    }

    return true;
}

function formatName(value) {
    let val = String(value || '').toUpperCase();
    // Replace comma followed by no space with comma and space
    val = val.replace(/,(\S)/g, ', $1');
    // Replace multiple spaces with a single space
    val = val.replace(/  +/g, ' ');
    return val;
}

function bindNameFormatter(selector) {
    document.querySelectorAll(selector).forEach(input => {
        input.value = formatName(input.value);
        input.addEventListener('input', (e) => {
            const start = e.target.selectionStart;
            const end = e.target.selectionEnd;
            e.target.value = formatName(e.target.value);
            e.target.setSelectionRange(start, end);
        });
    });
}




