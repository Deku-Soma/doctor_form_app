# Quick Template Signature Fix Guide

## Issue
Templates were checking for `{field}_base64` but signatures are stored without the suffix in the data structure.

## Solution
All templates should check if the field exists first, then use it directly in the data URI.

## Pattern for Single Signature
```html
{% if signature_data %}
    <img src="data:image/png;base64,{{ signature_data }}" alt="Signature" />
{% endif %}
```

## Pattern for Nested Signatures (in 'sign' object)
```html
{% if sign %}
    {% if sign.employee_signature %}
        <img src="data:image/png;base64,{{ sign.employee_signature }}" alt="Employee Signature" />
    {% endif %}
{% endif %}
```

## Forms to Check
- ✅ drug_testing.html - FIXED
- ⚠️ psychology.html - uses sign.employee_signature, sign.ohnp_signature
- ⚠️ musculoskeletal.html - uses sign.employee_signature, sign.ohnp_signature  
- ⚠️ vitamin_b.html - uses signature_data
- ⚠️ complete_wellbeing.html - uses signature_base64
- ⚠️ cwb_referral.html - uses practitioner_signature
- ⚠️ annexure3.html - uses practitioner_signature
- ⚠️ certificate_fitness.html - uses practitioner_signature
- ⚠️ heights_questionnaire.html - uses employee_signature_data, examiner_signature_data
- ⚠️ hot_cold_exposure.html - uses signature_data
- ⚠️ confined_spaces.html - uses signature_data
