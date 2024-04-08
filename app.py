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
    .master("local[*]") \
    .appName("Mortality Analysis") \
    .getOrCreate()

df = spark.read.csv("file:///home/ubuntu/data/mortality_age.csv", header=True, sep=",")

# Remove commas from the "Number of Deaths" and "Death Rate per 100,000" columns and cast them to appropriate types
df = df.withColumn("Number of Deaths", functions.regexp_replace(df["Number of Deaths"], ",", "").cast("int")) \
    .withColumn("Death Rate Per 100,000", functions.regexp_replace(df["Death Rate Per 100,000"], ",", "").cast("float"))
df.cache() #caching to improve performance

# SUPPORTING FUNCTIONS
def prepopulate_data():
    if not session.get('country_codes') and not session.get('age_group'):
        # Collect all distinct country codes, sort them, then convert df to rdd, then flatten each row into its constituent elements. 
        session['country_codes'] = df.select("Country Code").distinct().orderBy("Country Code").rdd.flatMap(lambda x: x).collect()

        # Collect all distinct age groups, sort them, then convert df to rdd, then flatten each row into its constituent elements. 
        session['age_group'] = df.select("Age Group").distinct().orderBy("Age Group").rdd.flatMap(lambda x: x).collect()

# ROUTES
@app.route('/', methods=['GET'])
def homepage(): 
    prepopulate_data()
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
        
        # Gather data on Number of Deaths
        df_grouped_1 = df_filtered.groupBy("Year").agg(functions.sum("Number of Deaths").alias("Total Deaths"))
        
        # Gather data on Death rate
        df_grouped_2 = df_filtered.groupBy("Year").agg(functions.sum("Death Rate Per 100,000").alias("Death Rate"))
        
        # Collect data from data frame
        data_1 = df_grouped_1.collect()
        data_2 = df_grouped_2.collect()
        
        x_vals = [row["Year"] for row in data_1]
        y1_vals = [row["Total Deaths"] for row in data_1]
        y2_vals = [row["Death Rate"] for row in data_2]

        # Create plot 1 
        fig, ax1 = plt.subplots()
        ax1.bar(x_vals, y1_vals)
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Number of Deaths')
        ax1.set_title("Number of {} Deaths by Year in {} ({})".format(gender, country_code, age_group))
        
        # Save plot1 in png format to send to frontend
        plot1_buf = io.BytesIO()
        plt.savefig(plot1_buf, format='png')
        plot1_buf.seek(0)
        plot1_base64 = base64.b64encode(plot1_buf.read()).decode('utf-8')
        plt.close(fig)  

        # Create plot 2
        fig, ax2 = plt.subplots()
        ax2.bar(x_vals, y2_vals)
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Death rate')
        ax2.set_title("Death rate per 100,000 for {} by Year in {} ({})".format(gender, country_code, age_group))

        # Save plot2 in png format to send to frontend
        plot2_buf = io.BytesIO()
        plt.savefig(plot2_buf, format='png')
        plot2_buf.seek(0)
        plot2_base64 = base64.b64encode(plot2_buf.read()).decode('utf-8')
        plt.close(fig)
        
        return render_template('oneAnalysis.html', country_codes = session.get('country_codes'), age_group = session.get('age_group'), plot1=plot1_base64, plot2=plot2_base64)
    return render_template('oneAnalysis.html', country_codes = session.get('country_codes'), age_group = session.get('age_group'), plot1=None, plot2=None)

@app.route('/allAnalysis', methods=['GET', 'POST'])
def allAnalysis():
    if request.method == 'POST':
        age_group = str(request.form['age_group'])
        gender = str(request.form['gender'])
        year = str(request.form['year'])
        
        df_filtered = df.filter((df["Age Group"] == age_group) & (df["Sex"] == gender) & (df["Year"] == year))
        
        # Gather data on Number of Deaths
        df_grouped_1 = df_filtered.groupBy("Country Code").agg(functions.sum("Number of Deaths").alias("Total Deaths"))
        
        # Gather data on Death rate
        df_grouped_2 = df_filtered.groupBy("Country Code").agg(functions.sum("Death Rate Per 100,000").alias("Death Rate"))
        
        # Collect data from data frame
        data_1 = df_grouped_1.collect()
        data_2 = df_grouped_2.collect()
        
        x_ticks = list(range(len(data_1)))  # Create numerical ticks for x-axis
        bar_width = 0.5
        
        x_vals = [row["Country Code"] for row in data_1]
        y1_vals = [row["Total Deaths"] for row in data_1]
        y2_vals = [row["Death Rate"] for row in data_2]

        # Create plot1 
        fig, ax1 = plt.subplots(figsize=(18, 7.5))
        ax1.set_title("Number of {} Deaths by Countries in {} ({})".format(gender, year, age_group))
        ax1.bar(x_ticks, y1_vals, width=bar_width)
        ax1.set_xlabel('Countries')
        ax1.set_ylabel('Number of Deaths')
        ax1.set_xticklabels([])    #no labels for x-axis
        plt.xlim([0, len(x_ticks)])
        
        # Add country codes on top of each bar
        for i, val in enumerate(y1_vals):
            if i % 2 == 0:
                #val + k must be sufficiently large compared to plot values in order to see the shift of the bar labels
                ax1.text(x_ticks[i] + bar_width/2, val + 4000, x_vals[i], ha='center', va='bottom', fontsize=5.5, rotation=90)
            else: 
                ax1.text(x_ticks[i] + bar_width/2, val + 1000, x_vals[i], ha='center', va='bottom', fontsize=5.5, rotation=90)
                
        # Save plot1 in png format to send to frontend
        plot1_buf = io.BytesIO()
        plt.savefig(plot1_buf, format='png')
        plot1_buf.seek(0)
        plot1_base64 = base64.b64encode(plot1_buf.read()).decode('utf-8')
        plt.close(fig)  

        # Create plot2
        fig, ax2 = plt.subplots(figsize=(18, 7.5))
        ax2.set_title("Death rate per 100,000 for {} by Countries in {} ({})".format(gender, year, age_group))
        ax2.bar(x_ticks, y2_vals, width=bar_width)
        ax2.set_xlabel('Countries')
        ax2.set_ylabel('Death rate')
        ax2.set_xticklabels([])  
        plt.xlim([0, len(x_ticks)]) 
        
        for i, val in enumerate(y2_vals):
            if i % 2 == 0:
                #val + k must be sufficiently large compared to plot values in order to see the shift of the bar labels
                ax2.text(x_ticks[i] + bar_width/2, val + 12, x_vals[i], ha='center', va='bottom', fontsize=5.5, rotation=90)
            else:
                ax2.text(x_ticks[i] + bar_width/2, val + 16, x_vals[i], ha='center', va='bottom', fontsize=5.5, rotation=90)

        # Save plot2 in png format to send to frontend
        plot2_buf = io.BytesIO()
        plt.savefig(plot2_buf, format='png')
        plot2_buf.seek(0)
        plot2_base64 = base64.b64encode(plot2_buf.read()).decode('utf-8')
        plt.close(fig)
        
        return render_template('allAnalysis.html', age_group = session.get('age_group'), plot1=plot1_base64, plot2=plot2_base64)
    return render_template('allAnalysis.html', age_group = session.get('age_group'), plot1=None, plot2=None)

@app.route('/compareCountries', methods=['GET', 'POST'])
def compareCountries():
    if request.method == 'POST':
        country_code1 = str(request.form['country_code1'])
        country_code2 = str(request.form['country_code2'])
        metric = str(request.form['metric'])  # New input for the selected metric
        
        # Filter the DataFrame for the selected countries
        df_filtered1 = df.filter(df["Country Code"] == country_code1)
        df_filtered2 = df.filter(df["Country Code"] == country_code2)
        
        # Gather data for the selected metric
        if metric == 'Total Deaths':
            # Gather data on Number of Deaths
            df_grouped_1 = df_filtered1.groupBy("Year").agg(functions.sum("Number of Deaths").alias("Total Deaths"))
            df_grouped_2 = df_filtered2.groupBy("Year").agg(functions.sum("Number of Deaths").alias("Total Deaths"))
        elif metric == 'Death Rate':
            # Gather data on Death rate
            df_grouped_1 = df_filtered1.groupBy("Year").agg(functions.sum("Death Rate Per 100,000").alias("Death Rate"))
            df_grouped_2 = df_filtered2.groupBy("Year").agg(functions.sum("Death Rate Per 100,000").alias("Death Rate"))
        elif metric == 'Infant Mortality Rate':
            # Filter the DataFrame for the age group 0-6 days
            df_infant_deaths1 = df_filtered1.filter(df_filtered1["Age Group"] == "0-6 days")
            df_infant_deaths2 = df_filtered2.filter(df_filtered2["Age Group"] == "0-6 days")
            
            # Calculate the total number of infant deaths
            total_infant_deaths1 = df_infant_deaths1.groupBy().agg(functions.sum("Number of Deaths").alias("Total Infant Deaths")).collect()[0]["Total Infant Deaths"]
            total_infant_deaths2 = df_infant_deaths2.groupBy().agg(functions.sum("Number of Deaths").alias("Total Infant Deaths")).collect()[0]["Total Infant Deaths"]
            
            # Create DataFrame for plotting
            df_grouped_1 = spark.createDataFrame([(country_code1, total_infant_deaths1)], ["Country Code", "Infant Mortality Rate"])
            df_grouped_2 = spark.createDataFrame([(country_code2, total_infant_deaths2)], ["Country Code", "Infant Mortality Rate"])
        
        # Collect data from data frames
        data_1 = df_grouped_1.collect()
        data_2 = df_grouped_2.collect()
        
        x_vals = [row["Year"] for row in data_1]  # Assuming the x-axis represents years
        y1_vals = [row[metric] for row in data_1]
        y2_vals = [row[metric] for row in data_2]

        # Create plot1 
        fig, ax1 = plt.subplots()
        ax1.plot(x_vals, y1_vals, label=country_code1)
        ax1.plot(x_vals, y2_vals, label=country_code2)
        ax1.set_xlabel('Year')
        ax1.set_ylabel(metric)
        ax1.set_title("{} Comparison between {} and {}".format(metric, country_code1, country_code2))
        ax1.legend()
        
        # Save plot in png format to send to frontend
        plot_buf = io.BytesIO()
        plt.savefig(plot_buf, format='png')
        plot_buf.seek(0)
        plot_base64 = base64.b64encode(plot_buf.read()).decode('utf-8')
        plt.close(fig)  

        return render_template('compareCountries.html', countries=session.get('country_codes',plot=plot_base64))
    
    return render_template('compareCountries.html', countries=session.get('country_codes'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)