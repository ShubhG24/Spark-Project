document.getElementById('analysisForm').addEventListener('change', function() {
    var countryCode = document.getElementById('age_group').value;
    var ageGroup = document.getElementById('gender').value;
    var gender = document.getElementById('year').value;

    if (countryCode && ageGroup && gender) {
        document.getElementById('submitButton').disabled = false;
    } else {
        document.getElementById('submitButton').disabled = true;
    }
});