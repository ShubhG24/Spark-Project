document.getElementById('compareForm').addEventListener('change', function() {
    var country1 = document.getElementById('country1').value;
    var country2 = document.getElementById('country2').value;
    var metric = document.getElementById('metric').value;

    if (country1 && country2 && metric) {
        document.getElementById('compareButton').disabled = false;
    } else {
        document.getElementById('compareButton').disabled = true;
    }
});
