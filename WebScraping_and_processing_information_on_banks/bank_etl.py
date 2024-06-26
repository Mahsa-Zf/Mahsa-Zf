# Importing the required libraries
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

# Known Entities
url="https://en.wikipedia.org/wiki/List_of_largest_banks"
table_attribs=['Name', 'MC_USD_Billion']
cv_path='./Largest_banks_data.csv'
db_name= 'Banks'
table_name='Largest_banks'

# Define a log_progress function
def log_progress(message):
    ''' This function logs the mentioned message of a given stage of the
    code execution to a log file. Function returns nothing'''
    timestamp_format = '%Y-%h-%d-%H:%M:%S'
    now=datetime.now()
    timestamp=now.strftime(timestamp_format)
    with open ("./code_log.txt","a") as file:
        file.write(timestamp+": "+message+"\n")

log_progress('Preliminaries complete. Initiating ETL process')

# Define an extract function for webscraping
def extract(url, table_attribs):
    ''' This function aims to extract the required
    information from the website and save it to a data frame. The
    function returns the data frame for further processing. '''
    page=requests.get(url).text
    data=BeautifulSoup(page,'html.parser')
    df=pd.DataFrame(columns=table_attribs)
    tables=data.find_all('table')
    rows=tables[2].find_all('tr')
    for row in rows[1:]:

        col=row.find_all('td')
        data_dict={
        'Name':col[1].get_text(separator=' ', strip=True),
        'MC_USD_Billion':col[2].contents[0].strip()
        }
        df1=pd.DataFrame(data_dict,index=[0])
        df=pd.concat([df,df1],ignore_index=True)
    return df
df=extract(url, table_attribs)
df

log_progress('Data extraction complete. Initiating Transformation process')

# Transforming the scraped data to add other currencies
def transform(df, csv_path):
    ''' This function accesses the CSV file for exchange rate
    information, and adds three columns to the data frame, each
    containing the transformed version of Market Cap column to
    respective currencies'''
    df['MC_USD_Billion']=df['MC_USD_Billion'].astype(float)
    rate=pd.read_csv('/content/exchange_rate.csv')
    df['MC_GBP_Billion']= np.round(df['MC_USD_Billion']*rate[rate.Currency=='GBP']['Rate'][1],2)
    df['MC_EUR_Billion']= np.round(df['MC_USD_Billion']*rate[rate.Currency=='EUR']['Rate'][0],2)
    df['MC_INR_Billion']= np.round(df['MC_USD_Billion']*rate[rate.Currency=='INR']['Rate'][2],2)

    return df

transform(df,'/content/exchange_rate.csv')
log_progress('Data transformation complete. Initiating loading process')

# Creating a CSV file
def load_to_csv(df, output_path):
    ''' This function saves the final data frame as a CSV file in
    the provided path. Function returns nothing.'''
    df.to_csv(output_path, index=False)

load_to_csv(df, cv_path)
log_progress('Data saved to CSV file')

# Loading the table to a database
def load_to_db(df, sql_connection, table_name):
    ''' This function saves the final data frame to a database
    table with the provided name. Function returns nothing.'''
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

sql_connection=sqlite3.connect(db_name)
load_to_db(df, sql_connection, table_name)
log_progress('Data saved to database')

# Running a query on the created table
def run_query(query_statement, sql_connection):
    ''' This function runs the query on the database table and
    prints the output on the terminal. Function returns nothing. '''
    ''' Here, you define the required entities and call the relevant
    functions in the correct order to complete the project. Note that this
    portion is not inside any function.'''

    print(query_statement)
    query_output=pd.read_sql_query(query_statement, sql_connection)
    print(query_output)

log_progress('Data loaded to Database as table. Running the query')

query_statement="""
SELECT * FROM Largest_banks
"""
run_query(query_statement, sql_connection)

log_progress('Process Complete.')

sql_connection.close()
