import pandas as pd
import sqlite3
import re
import numpy as np
from flask import Flask, jsonify, request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from

def connectDatabase():
  connect_db = sqlite3.connect('data/gold_challenge.db')
  cursor = connect_db.cursor()

  create_table_tweet = '''CREATE TABLE if not exists tweet(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tweet TEXT);'''
  
  create_table_alay = '''CREATE TABLE if not exists alay(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alay TEXT,
    fix_alay TEXT);'''

  create_table_abusive = '''CREATE TABLE if not exists abusive(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    abusive TEXT);'''

  cursor.execute(create_table_tweet)
  cursor.execute(create_table_alay)
  cursor.execute(create_table_abusive)
  return connect_db

def syncDatabase():
  connect_db = connectDatabase()

  # file_tweet = r'E:/folder-file/future/python/binarAcademy/gold/data/data.csv'
  file_abusive = r'E:/folder-file/future/python/binarAcademy/gold/data/abusive.csv'
  file_alay = r'E:/folder-file/future/python/binarAcademy/gold/data/new_kamusalay.csv'

  # df_tweet = pd.read_csv(file_tweet, usecols=['Tweet'], encoding= "ISO-8859-1")
  df_abusive = pd.read_csv(file_abusive, encoding= "ISO-8859-1")
  df_alay = pd.read_csv(file_alay, encoding= "ISO-8859-1")

  # df_tweet.to_sql('tweet', connect_db, if_exists='replace', index=False)
  df_abusive.to_sql('abusive', connect_db, if_exists='replace', index=False)
  df_alay.to_sql('alay', connect_db, if_exists='replace', index=False)
  print('database connected')

def do_clean_text(text, list_abusive, list_alay, list_fix_alay):
  splitted_text = re.split(" ", text)
  for word in splitted_text:
    if word in list_abusive:
      splitted_text[splitted_text.index(word)] = splitted_text[splitted_text.index(word)].replace(word, '**censored**')
    elif word in list_alay:
      a = list_alay.index(word)
      splitted_text[splitted_text.index(word)] = splitted_text[splitted_text.index(word)].replace(word, list_fix_alay[a])
    text_clean = " ".join(splitted_text)

  return text_clean

def clean_data(data):
  cursor = connectDatabase().cursor()
  syncDatabase()

  db_abusive = cursor.execute(f'select abusive from abusive').fetchall()
  db_abusive = pd.DataFrame(db_abusive, columns=['abusive'])

  db_alay = cursor.execute(f'select alay, fix_alay from alay').fetchall()
  db_alay = pd.DataFrame(db_alay, columns=['alay', 'fix_alay'])
  
  list_abusive = db_abusive['abusive'].str.lower().tolist()
  list_alay = db_alay['alay'].str.lower().tolist()
  list_fix_alay = db_alay['fix_alay'].str.lower().tolist()

  data = pd.DataFrame(data, columns=['Tweet'])
  list_data = data['Tweet'].str.lower().tolist()

  for text in list_data:
    text_clean = do_clean_text(text, list_abusive, list_alay, list_fix_alay)
    list_data[list_data.index(text)] = text_clean

  return list_data

app = Flask(__name__)

# ==================================== swagger configuration
app.json_encoder = LazyJSONEncoder

swagger_template = dict(
    info = {
        'title': LazyString(lambda:'API Documentation for Data Processing and Modeling'),
        'version': LazyString(lambda:'1.0.0'),
        'description': LazyString(lambda:'Dokumentasi API untuk Data Processing dan Modeling')
    }, host = LazyString(lambda: request.host)
)

swagger_config = {
        "headers":[],
        "specs":[
            {
            "endpoint":'docs',
            "route":'/docs.json'
            }
        ],
        "static_url_path":"/flasgger_static",
        "swagger_ui":True,
        "specs_route":"/docs/"
    }

swagger = Swagger(app, template=swagger_template, config=swagger_config)

# ======================================= buat endpoint API
@swag_from('docs/text_processing.yml', methods=['POST'])
@app.route('/text-cleansing', methods=['POST'])
def text_clean():
  text = request.form.get('text')

  syncDatabase()
  cursor = connectDatabase().cursor()

  db_abusive = cursor.execute(f'select abusive from abusive').fetchall()
  db_abusive = pd.DataFrame(db_abusive, columns=['abusive'])

  db_alay = cursor.execute(f'select alay, fix_alay from alay').fetchall()
  db_alay = pd.DataFrame(db_alay, columns=['alay', 'fix_alay'])
  
  list_abusive = db_abusive['abusive'].str.lower().tolist()
  list_alay = db_alay['alay'].str.lower().tolist()
  list_fix_alay = db_alay['fix_alay'].str.lower().tolist()

  data = do_clean_text(text, list_abusive, list_alay, list_fix_alay)

  json_response = { 
        'status_code':200, 
        'description':'teks yang sudah diproses', 
        'data': data
        }

  response_data = jsonify(json_response)
  return response_data

@swag_from('docs/upload_file.yml', methods=['POST'])
@app.route('/upload-file', methods=['POST'])
def upload():
  file = request.files['upfile']
  
  if (file) :
    print("file uploaded")
    df_tweet = pd.read_csv(file, usecols=['Tweet'], encoding= "ISO-8859-1")
    data = clean_data(df_tweet)
    
  else :
    data = "file not uploaded yet"

  json_response = { 
        'status_code':200, 
        'description':'teks yang sudah diproses', 
        'data': data
      }
  
  response = jsonify(json_response)
  return response

if __name__ == "__main__":
  app.run()
