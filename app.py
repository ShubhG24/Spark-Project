from flask import Flask, render_template, redirect, session, request
from pyspark.sql import SparkSession, functions
import matplotlib
matplotlib.use('Agg')  # Agg is a non-interactive backend that does not require a display 

import matplotlib.pyplot as plt
import io
import base64

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

@app.route('/oneAnalysis', methods=['GET', 'POST'])
def oneAnalysis():
    if request.method == 'POST':
        country_code = str(request.form['country_code'])
        age_group = str(request.form['age_group'])
        gender = str(request.form['gender'])
        
        df_filtered = df.filter((df["Country Code"] == country_code) & (df["Age Group"] == age_group) & (df["Sex"] == gender))
        df_grouped = df_filtered.groupBy("Year").agg(functions.sum("Number of Deaths").alias("Total Deaths"))
        data = df_grouped.collect()
        
        x_vals = [row["Year"] for row in data]
        y_vals = [row["Total Deaths"] for row in data]
        
        # Create plot using matplotlib
        fig, ax = plt.subplots()
        ax.bar(x_vals, y_vals)
        plt.xlabel('Year')
        plt.ylabel('Number of Deaths')
        plt.title("Number of {} Deaths by Year in {} ({})".format(gender, country_code, age_group))
        
        # Send the plot to frontend
        plot_buf = io.BytesIO()
        plt.savefig(plot_buf, format='png')
        plot_buf.seek(0)
        plot_base64 = base64.b64encode(plot_buf.read()).decode('utf-8')
        plt.close()  

        return render_template('oneAnalysis.html', plot=plot_base64)
    return render_template('oneAnalysis.html', plot=None)

@app.route('/allAnalysis', methods=['GET'])
def allAnalysis():
    prepopulate()
    return render_template('allAnalysis.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)