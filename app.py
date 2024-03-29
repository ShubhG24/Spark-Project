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
        
        # Gather data on Number of Deaths
        df_filtered = df.filter((df["Country Code"] == country_code) & (df["Age Group"] == age_group) & (df["Sex"] == gender))
        df_grouped = df_filtered.groupBy("Year").agg(functions.sum("Number of Deaths").alias("Total Deaths"))
        data = df_grouped.collect()
        
        x_vals = [row["Year"] for row in data]
        y1_vals = [row["Total Deaths"] for row in data]
        
        # Create plot 1 
        fig, ax1 = plt.subplots()
        ax1.bar(x_vals, y1_vals)
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Number of Deaths')
        ax1.set_title("Number of {} Deaths by Year in {} ({})".format(gender, country_code, age_group))
        
        # Send the plot1 to frontend
        plot1_buf = io.BytesIO()
        plt.savefig(plot1_buf, format='png')
        plot1_buf.seek(0)
        plot1_base64 = base64.b64encode(plot1_buf.read()).decode('utf-8')
        plt.close(fig)  
        
        #Gather data on Death rate
        df_filtered = df.filter((df["Country Code"] == country_code) & (df["Age Group"] == age_group) & (df["Sex"] == gender))
        df_grouped = df_filtered.groupBy("Year").agg(functions.sum("Death Rate Per 100,000").alias("Death Rate"))
        data = df_grouped.collect()
        
        y2_vals = [row["Death Rate"] for row in data]
        # Create plot 2
        fig, ax2 = plt.subplots()
        ax2.bar(x_vals, y2_vals)
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Death rate')
        ax2.set_title("Death rate per 100,000 for {} by Year in {} ({})".format(gender, country_code, age_group))

        # Send plot2 to frontend
        plot2_buf = io.BytesIO()
        plt.savefig(plot2_buf, format='png')
        plot2_buf.seek(0)
        plot2_base64 = base64.b64encode(plot2_buf.read()).decode('utf-8')
        plt.close(fig)
        
        return render_template('oneAnalysis.html', plot1=plot1_base64, plot2=plot2_base64)
    return render_template('oneAnalysis.html', plot1=None, plot2=None)

@app.route('/allAnalysis', methods=['GET'])
def allAnalysis():
    return render_template('allAnalysis.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)