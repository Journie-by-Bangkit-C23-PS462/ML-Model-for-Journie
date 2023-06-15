from keras.models import load_model
from scipy.spatial import distance_matrix
import pandas as pd
from python_tsp.heuristics import solve_tsp_simulated_annealing

#This function is used to determine route of the tourist after we get the recommended result from the model
def prediction_model(age, city, category, total_day):
    #load dataset
    tourist_df = pd.read_csv("https://raw.githubusercontent.com/Journie-by-Bangkit-C23-PS462/dataset_tourist/main/tourism_with_id_duration.csv")

    #load model (recommendation model)
    model = load_model("plan_model.h5")
    
    #create dataframe for the user input
    value = age
    column = pd.Series([value] * 437, name='Age')
    df = pd.DataFrame()
    df = pd.concat([df, column], axis=1)
    test_user = df
    test_user["Place_Id"] = tourist_df["Place_Id"]
    test_user["score"] = model.predict([test_user["Age"], tourist_df["Place_Id"]])


    #merge the result with the dataset
    hasil = test_user[["Place_Id", "score"]].merge(
        tourist_df[["Place_Name", "Category", "City", "Lat", "Long"]], left_on="Place_Id", 
        right_index=True
    ).sort_values("score", ascending=False)

    #filter the result based on the user input
    jumlah_data = total_day * 5
    filtered_hasil = hasil[ (hasil["City"] == city) & (hasil["Category"].isin(category))]
    filtered_hasil.drop_duplicates(subset=["Place_Name"], inplace=True)
    final_result = filtered_hasil[:jumlah_data]

    #create the route based on the result
    matrix = final_result[["Lat", "Long"]].values
    d = distance_matrix(matrix, matrix)
    permutation_distance, distance = solve_tsp_simulated_annealing(d)

    city_order = final_result.iloc[permutation_distance]["Place_Id"].values

    route = []
    for i in permutation_distance:
        route.append(final_result.iloc[i]["Place_Id"])
    route.append(final_result.iloc[0]["Place_Id"])
    route_df = pd.DataFrame(route, columns=["Place_Id"])
    result_ftp = route_df[["Place_Id"]].merge(
       tourist_df[["Place_Name", "Category", "City", "Lat", "Long", "Price", "Duration", "Description", "image_link"]], left_on="Place_Id", 
       right_index=True
    )

    #create the recommendation based on the route
    result_ftp.drop_duplicates(subset=["Place_Name"], inplace=True)
    duration_temp = 0
    start = 0
    mid = 0
    end = 0
    for i in range(jumlah_data):
        duration_temp += result_ftp.iloc[i]["Duration"]
        if ((duration_temp >= 240) & (start == 0)):
            start = i + 1
            duration_temp = 0
        if ((duration_temp >= 240) & (mid == 0) & (total_day >= 2)):
            mid = i + 1
            duration_temp = 0
        if ((duration_temp >= 240) & (end == 0) & (total_day >= 3)):
            end = i + 1
            break

    day_one = result_ftp[:start]
    day_two = result_ftp[start:mid]
    day_three = result_ftp[mid:end]
    recommendation = day_one.to_dict('records'), day_two.to_dict('records'), day_three.to_dict('records')
    #recommendation = result_ftp.to_dict('records')
    return recommendation