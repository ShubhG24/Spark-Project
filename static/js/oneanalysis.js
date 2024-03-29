document.getElementById('country_code').addEventListener('change', function() {
    var countryCode = this.value;
    if (countryCode) {
        document.getElementById('ageGroupContainer').style.display = 'block';
        document.getElementById('genderContainer').style.display = 'block';
    } else {
        document.getElementById('ageGroupContainer').style.display = 'none';
        document.getElementById('genderContainer').style.display = 'none';
    }
});

document.getElementById('analysisForm').addEventListener('change', function() {
    var countryCode = document.getElementById('country_code').value;
    var ageGroup = document.getElementById('age_group').value;
    var gender = document.getElementById('gender').value;

    if (countryCode && ageGroup && gender) {
        document.getElementById('submitButton').disabled = false;
    } else {
        document.getElementById('submitButton').disabled = true;
    }
});
