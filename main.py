from flask import Flask, request
import explore_place_recommendation_journie as explore_model
import modelfix
import json
import pg8000
import pandas as pd
import numpy as np
import os

app = Flask(__name__)


conn = pg8000.connect(
    host = "34.128.80.91",
    database = "capstone-ML",
    port = 5432,
    user = "postgres",
    password = "journie123"
)
  
  
@app.route('/')
def hello_world():
    return 'Hello World'


@app.route('/planmodel', methods=['POST'])
def predict2():
    req_data = request.get_json()
    city = req_data['city']
    if city != "Jakarta" and city != "Bandung" and city != "Yogyakarta" and city != "Surabaya" and city != "Bali":
        status = {}
        status['status'] = False
        return json.dumps(status)
    category = []
    age = req_data['age']
    username = req_data['username']
    if age > 40:
        age = 30 + (age % 10)
        if age == 30:
            age = 40
    total_day = req_data['duration']
    if req_data['bahari'] == True:
        category.append("Bahari")
    if req_data['budaya'] == True:
        category.append("Budaya")
    if req_data['tamanHiburan'] == True:
        category.append("Taman Hiburan")
    if req_data['pusatPerbelanjaan'] == True:
        category.append("Pusat Perbelanjaan")
    if req_data['tempatIbadah'] == True:
        category.append("Tempat Ibadah")
    if req_data['bahari'] == False and req_data['budaya'] == False and req_data['tamanHiburan'] == False and req_data['pusatPerbelanjaan'] == False and req_data['tempatIbadah'] == False:
        status = {}
        status['status'] = False
        return json.dumps(status)
    
    hasil = modelfix.prediction_model(age, city, category, total_day)
    if hasil == None:
        status = {}
        status['status'] = False
        return json.dumps(status)
    place_ids = []
    for lst in hasil:
        inner_ids = []
        for d in lst:
            inner_ids.append(d['Place_Id'])
        place_ids.append(inner_ids)
    max_length = max(len(lst) for lst in place_ids)
    place_ids_padded = [lst + [None] * (max_length - len(lst)) for lst in place_ids]

    cur = conn.cursor()
    cur.execute("""
    INSERT INTO user_plan (user_name, place_id, issaved)
    VALUES (%s, %s, false);
    """, (username, place_ids_padded))
     # Commit the transaction
    conn.commit()
    # Close the cursor and connection
    cur.close()
    data = {}
    data['data'] = hasil
    data['status'] = True
    return json.dumps(data)

@app.route('/explore_jakarta', methods=['GET'])
def jakarta():
    explore_result = explore_model.explore("Jakarta", 25)
    data = {}
    data['data'] = explore_result
    return json.dumps(data)

@app.route('/explore_bandung', methods=['GET'])
def bandung():
    explore_result = explore_model.explore("Bandung", 25)
    data = {}
    data['data'] = explore_result
    return json.dumps(data)

@app.route('/explore_surabaya', methods=['GET'])
def surabaya():
    explore_result = explore_model.explore("Surabaya", 25)
    data = {}
    data['data'] = explore_result
    return json.dumps(data)

@app.route('/explore_jogja', methods=['GET'])
def jogja():
    explore_result = explore_model.explore("Yogyakarta", 25)
    data = {}
    data['data'] = explore_result
    return json.dumps(data)

@app.route('/explore_semarang', methods=['GET'])
def semarang():
    explore_result = explore_model.explore("Semarang", 25)
    data = {}
    data['data'] = explore_result
    return json.dumps(data)


@app.route('/activeplan', methods=['POST'])
def activeplan():
    tourist_df = pd.read_csv("https://raw.githubusercontent.com/Journie-by-Bangkit-C23-PS462/dataset_tourist/main/tourism_with_id_duration.csv")
    req_data = request.get_json()
    username = req_data['username']
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_plan WHERE user_name = %s AND issaved = true", (username,))
    rows = cur.fetchall()
    num_plan = len(rows)
    for i in range(num_plan):
        num_day = len(rows[i][1])
        
    day_one = []
    day_two = []
    day_three = []
    plan = {}

    for i in range(num_plan):
        for j in range(num_day):
            if j == 0:
                day_one = (rows[i][2][j])
                day_one = filter(lambda x: x is not None, day_one)
                day_one = pd.DataFrame(day_one, columns=['Place_Id'])
                day_one = pd.merge(day_one, tourist_df, on='Place_Id')
            elif j == 1:
                day_two = (rows[i][2][j])
                day_two = filter(lambda x: x is not None, day_two)
                day_two = pd.DataFrame(day_two, columns=['Place_Id'])
                day_two = pd.merge(day_two, tourist_df, on='Place_Id')
            elif j == 2:
                day_three = (rows[i][2][j])
                day_three = filter(lambda x: x is not None, day_three)
                day_three = pd.DataFrame(day_three, columns=['Place_Id'])
                day_three = pd.merge(day_three, tourist_df, on='Place_Id')
            
        result = day_one.to_dict('records'), day_two.to_dict('records'), day_three.to_dict('records')
        plan [i] = result
    if plan == {}:
        status = {}
        status['status'] = False
        return json.dumps(status)
    data = {}
    data['data'] = plan
    data['status'] = True
    return json.dumps(data)

@app.route('/savedplan', methods=['POST'])
def savedplan():
    req_data = request.get_json()
    plan_id = req_data['plan_id']
    cur = conn.cursor()
    cur.execute("UPDATE user_plan SET issaved = true WHERE plan_id = %s", (plan_id,))
    conn.commit()
    cur.close()
    data = {}
    data['data'] = "Plan Saved"
    return json.dumps(data)

@app.route('/planhistory', methods=['POST'])
def planhistory():
    tourist_df = pd.read_csv("https://raw.githubusercontent.com/Journie-by-Bangkit-C23-PS462/dataset_tourist/main/tourism_with_id_duration.csv")
    req_data = request.get_json()
    username = req_data['username']
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_plan WHERE user_name = %s", (username,))
    rows = cur.fetchall()
    if len(rows) == 0:
        status = {}
        status['status'] = False
        return json.dumps(status)
    num_plan = len(rows)
    for i in range(num_plan):
        num_day = len(rows[i][1])
        
    day_one = []
    day_two = []
    day_three = []
    plan = {}

    for i in range(num_plan):
        for j in range(num_day):
            if j == 0:
                day_one = (rows[i][2][j])
                day_one = filter(lambda x: x is not None, day_one)
                day_one = pd.DataFrame(day_one, columns=['Place_Id'])
                day_one = pd.merge(day_one, tourist_df, on='Place_Id')
            elif j == 1:
                day_two = (rows[i][2][j])
                day_two = filter(lambda x: x is not None, day_two)
                day_two = pd.DataFrame(day_two, columns=['Place_Id'])
                day_two = pd.merge(day_two, tourist_df, on='Place_Id')
            elif j == 2:
                day_three = (rows[i][2][j])
                day_three = filter(lambda x: x is not None, day_three)
                day_three = pd.DataFrame(day_three, columns=['Place_Id'])
                day_three = pd.merge(day_three, tourist_df, on='Place_Id')
            
        result = day_one.to_dict('records'), day_two.to_dict('records'), day_three.to_dict('records')
        plan [i] = result
    data = {}
    data['data'] = plan
    data['status'] = True
    return json.dumps(data)

@app.route('/deleteplan', methods=['POST'])
def deleteplan():
    req_data = request.get_json()
    plan_id = req_data['plan_id']
    cur = conn.cursor()
    cur.execute("DELETE FROM user_plan WHERE plan_id = %s", (plan_id,))
    if cur.rowcount == 0:
        status = {}
        status['status'] = False
        return json.dumps(status)
    conn.commit()
    cur.close()
    data = {}
    data['data'] = "Plan Deleted"
    data['status'] = True
    return json.dumps(data)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')