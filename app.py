from flask import Flask, render_template, redirect, session
from pyspark.sql import SparkSession

app = Flask(__name__, static_url_path="")
app.secret_key = 'spark'

spark = SparkSession \
    .builder \
    .master("local") \
    .appName("Mortality Analysis") \
    .getOrCreate()

df = spark.read.csv("file:///home/ubuntu/data/mortality_age.csv", header=True, sep=",")

# ROUTES
@app.route('/', methods=['GET'])
def homepage(): 
    return render_template('home.html')

@app.route('/close', methods=['GET'])
def close():
    spark.stop()
    return redirect('http://www.google.com')

@app.route('/oneAnalysis', methods=['GET'])
def oneAnalysis():
    if not session.get('country_codes'):
        session['country_codes'] = df.select("Country Code").distinct().rdd.flatMap(lambda x: x).collect()
    return render_template('oneAnalysis.html', country_codes=session.get('country_codes'))

@app.route('/allAnalysis', methods=['GET'])
def allAnalysis():
    return render_template('allAnalysis.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)