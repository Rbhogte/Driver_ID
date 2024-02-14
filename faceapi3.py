"""
Library Imports
"""

import requests
import hashlib
import time
import json
import base64
import os
import cv2
from flask import Flask, render_template,request, Response,session
from flask import redirect, url_for
from flask import jsonify
import datetime
from dotenv import load_dotenv


"""
Constants and Global Variables
"""
load_dotenv(override=True)
temp_URL = None
image_path = None
output_directory = os.getenv('OUTPUT_DIRECTORY')
local_file_path = os.getenv('LOCAL_FILE_PATH')
account_sid = os.getenv('ACCOUNT_SID')
auth_token = os.getenv('AUTH_TOKEN')
api_key = os.getenv('API_KEY')
base_url = os.getenv('BASE_URL')
face_reg_base_url = os.getenv('FACE_REG_BASE_URL')
face_reg_api_key = os.getenv('FACE_REG_API_KEY')
face_reg_secret_key = os.getenv('FACE_REG_SECRET_KEY')
face_reg_version = os.getenv('FACE_REG_VERSION')
length = 6
content = "ALL"
#endpoint_id = 122381
endpoint_id = None
is_device_online = None
summary = None
cached_faces_data = None
app = Flask(__name__)
app.secret_key = '0ac8ba54425cbefd8f9b737bf9730c47'


def send_status_request(endpoint_id):
    print(endpoint_id)
    url = f"{base_url}/endpoints/{endpoint_id}"
    headers = {
        "SAI-Key": api_key,
        "accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    response_data = response.json()
    if response_data['isOnline']:
        return True,'Online'
    else:
        return False,'Offline'
def send_recording_request(length, content, endpoint_id,summary,start_time):
    """
    Sends a recording request to the specified endpoint using the provided API key, length, content, endpoint ID, summary, and start time.

    Parameters:
    - api_key (str): The API key for authentication.
    - length (int): The length of the recording.
    - content (str): The content of the recording.
    - endpoint_id (str): The ID of the endpoint where the recording will be sent.
    - summary (str): A summary of the recording request.
    - start_time (str): The start time of the recording.

    Returns:
    - response_data (dict): The response data from the recording request.
    - requested_id (str): The ID of the requested recording.
    """
    url = f"{base_url}/recording-requests"
    headers = {
        "SAI-Key": api_key,
        "accept": "application/json",
        "content-type": "application/json"
    }
    print('WITHIN send recording',api_key, length, content, endpoint_id,summary,start_time)
    data = {
        "length": length,
        "content": content,
        "endpointId": endpoint_id,
        "summary":summary,
        "start_time":start_time
    }
    #print("jsoan data",data)
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()
   
    requested_id = ""
   
    if 'requestId' in response_data:
        requested_id = response_data['requestId']
   
    return response_data, requested_id  
def get_recording_request(recording_request_id):
    """
    Retrieves recording request data based on the given API key and recording request ID.

    Args:
        api_key (str): The API key for authentication.
        recording_request_id (str): The ID of the recording request.

    Returns:
        dict: A dictionary containing the recording request data, including the request ID, endpoint ID, status, summary, start time, length, and content; or an error message if the request fails.
    """
    BASE_URL = f"{base_url}/recording-requests/{recording_request_id}"
    headers = {
        "accept": "application/json",
        "SAI-Key": api_key
    }
   
    try:
        #response = requests.post(base_url, headers=headers, json=data)
        response = requests.get(BASE_URL, headers=headers)
        #response = requests.patch(base_url, headers=headers, json=data)
        if response.status_code == 200:
            recording_request_data = response.json()
            request_id = recording_request_data.get("requestId")
            endpoint_id = recording_request_data.get("endpointId")
            status = recording_request_data.get("status")
            summary = recording_request_data.get("summary")
            start_time = recording_request_data.get("startTime")
            length = recording_request_data.get("length")
            content = recording_request_data.get("content")
            return {
                "Request ID": request_id,
                "Endpoint ID": endpoint_id,
                "Status": status,
                "Summary": summary,
                "Start Time": start_time,
                "Length": length,
                "Content": content
            }
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred: {e}"}
def get_recordings(start_timestamp, end_timestamp):
    """
    Retrieves recordings from a given endpoint within a specified time range.

    Args:
        base_url1 (str): The base URL for the API.
        headers (dict): The headers for the request.
        start_timestamp (int): The start timestamp for the time range.
        end_timestamp (int): The end timestamp for the time range.

    Returns:
        str: The URL of the first matching recording, or an empty string if no matching recordings are found.
    """
    global temp_URL
    headers = {
    "accept": "application/json",
    "SAI-Key": api_key
    } 
    params = {
        "from": start_timestamp,
        "to": end_timestamp,
        "client": 1
    }
 
    try:
        endpoint_id = session.get('endpoint_id')
        print(base_url)
        BASE_URL = f"{base_url}/endpoints/{endpoint_id}/recordings"
        print('BASE',BASE_URL)
        response = requests.get(BASE_URL, headers=headers, params=params)
        if response.status_code == 200:
            recordings_data = response.json()
            recordings = recordings_data.get("recordings", [])
            filtered_recordings = [recording for recording in recordings if recording["source"] == "vid_2" and recording["type"] == "VIDEO"]
 
            if filtered_recordings:
                first_matching_recording = filtered_recordings[0]
                temp_URL = first_matching_recording["url"]
                print("Recording ID:", first_matching_recording["id"])
                print("Start Timestamp:", first_matching_recording["startTimestamp"])
                print("End Timestamp:", first_matching_recording["endTimestamp"])
                print("Source:", first_matching_recording["source"])
                print("Type:", first_matching_recording["type"])
                print("URL:", temp_URL)
                print("-" * 40)
            else:
                print("No recordings matching the criteria found.")
 
        else:
            print("Request failed with status code:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
    return temp_URL

@app.route('/', methods=['GET', 'POST'])
def index():
        print(face_reg_version)
        return render_template('index1.html')
@app.route('/choosecamera', methods=['POST'])
def choosecamera():
        """
        A function to handle the POST request for choosing a camera. It retrieves the selected camera from the request form, sets the endpoint ID, and updates the session with the endpoint ID. Finally, it returns a JSON response with the status and the endpoint ID.
        """
        if request.method == 'POST':
            selected_camera = request.form.get('selectedCamera')
            endpoint_id = selected_camera
            print(selected_camera)
            print(endpoint_id)
            session['endpoint_id'] = endpoint_id
            print(session['endpoint_id'])
            return jsonify({'status': 'success', 'endpoint_id': endpoint_id})
@app.route('/check_status', methods=['GET'])
def check_device_status():
    """
    A function to check the status of a device and return its current status.
    """
    # current_timestamp = int(datetime.datetime.now().timestamp() * 1000)
    # start_time = current_timestamp
    endpoint_id = session.get('endpoint_id')
    # global device_status
    # response_data, requested_id = send_recording_request(length, content, endpoint_id,summary,start_time)
    isOnline, device_status = send_status_request(endpoint_id)
    session['is_device_online'] = isOnline
    print(device_status)
    return jsonify({'device_status': device_status})
    # print("Response Data:", response_data)
    # print("Requested ID:", requested_id)
    # if not requested_id:
    #     device_status = "Offline"
    #     '''message = client.messages.create(
    #     #from_='+12563048332',
    #     from_='+17157695307',
    #     body='Device is offline',
    #     to='+919822442523'
    #     #to='+917775058954'
    #     )'''
    #     print("Device Status:", device_status)
    #     return jsonify({'device_status': device_status})
   
    # else:
    #     device_status = "Online"
    #     print(requested_id)
    #     print("Device Status:", device_status)
    #     return jsonify({'device_status': device_status, 'requested_id': requested_id})
   
   
# face_reg_base_url = "https://frec.edgetensor.ai"  
# face_api_key = "7fea772b-d454-49ab-a40d-338318c9ed3f"
# secret_key = "1PY9UWDu1giCPEGDZkB6guVhYdybnx2SMK7xzLVJpnDjBMKtuFe52Q8n2T6N6CKO"
# version = "v2"  
 
def generate_sha512_hash(data):
    return hashlib.sha512(data.encode("utf-8")).hexdigest()
 
def get_headers():
    timestamp = str(int(time.time() * 1000))
    sha512_hash = generate_sha512_hash(face_reg_api_key + face_reg_secret_key + timestamp)
   
    headers = {
        "X-API-KEY": face_reg_api_key,
        "X-TIMESTAMP": timestamp,
        "X-SHA512-HASH": sha512_hash
    }
    return headers
def get_faces(faceset_id, limit, offset):
    endpoint = f"{face_reg_base_url}/{face_reg_version}/faces"
    #print("face_reg_base_url",face_reg_base_url)
    headers = get_headers()
 
    params = {
        "faceset_id": faceset_id,
        "limit": limit,
        "offset": offset
    }
 
    try:
        response = requests.get(endpoint, headers=headers, params=params)
 
        if response.status_code == 200:
            faces_data = response.json()
            cached_faces_data = faces_data
            #print("cached_faces_data",cached_faces_data)
            return faces_data
        else:
            return {"error": "Failed to retrieve faces", "status_code": response.status_code}
 
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred: {e}"}
 
#faceset_id_param = '81f151ad-cb9b-47a1-be10-3d3b2cb03120'
faceset_id_param ='67616902-2903-4c7d-836e-3d4b18dfb6a3'
limit_param = 10
offset_param = 0  
faces_data = get_faces(faceset_id=faceset_id_param, limit=limit_param, offset=offset_param)
def perform_face_lookup(lookup_data):
    endpoint = f"{face_reg_base_url}/{face_reg_version}/lookups/face"
    # endpoint ="https://frec.edgetensor.ai/v3/lookups/face"
    headers = get_headers()
    print("ENDPOINT",endpoint)
    try:
        response = requests.post(endpoint, json=lookup_data, headers=headers)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred: {e}"}
 
def perform_face_landmark_lookup(lookup_data):
    endpoint = f"{face_reg_base_url}/{face_reg_version}/lookups/landmark"
    # endpoint = "https://frec.edgetensor.ai/v3/lookups/landmark"
    headers = get_headers()
    try:
        response = requests.post(endpoint, json=lookup_data, headers=headers)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred: {e}"}
 
 
@app.route('/delete_face', methods=['POST'])
def delete_face():
    API_KEY = "7fea772b-d454-49ab-a40d-338318c9ed3f"
    SECRET_KEY = "1PY9UWDu1giCPEGDZkB6guVhYdybnx2SMK7xzLVJpnDjBMKtuFe52Q8n2T6N6CKO"
    name = request.form['name']
    faces_data = get_faces(faceset_id=faceset_id_param, limit=limit_param, offset=offset_param)
 
    target_face_id = None
    for face in faces_data:
        if face['name'] == name:
            target_face_id = face.get("id_", "N/A")
            break
 
    if target_face_id is not None:
        timestamp = str(int(time.time() * 1000))
        sha_512_hash = hashlib.sha512((API_KEY + SECRET_KEY + timestamp).encode("utf-8")).hexdigest()
 
        headers = {
            "X-API-KEY": API_KEY,
            "X-TIMESTAMP": timestamp,
            "X-SHA512-HASH": sha_512_hash
        }
 
        endpoint = f"{face_reg_base_url}/{face_reg_version}/faces/{target_face_id}"
        url = endpoint.format(version=face_reg_version, id_=target_face_id)
 
        response = requests.delete(url, headers=headers)
 
        if response.status_code == 200:
            result = "Face deleted successfully"
        else:
            result = f"Failed to delete face. Status code: {response.status_code}"
            result += f"<br>Response content: {response.content}"
    else:
        result = f"Face with name '{name}' not found"
 
    return jsonify({'result': result})
@app.route('/display_faces',methods=['GET','POST'])
def display_faces():
    faceset_id_param = '67616902-2903-4c7d-836e-3d4b18dfb6a3'
    limit_param = 100
    offset_param = 0
    faces_data = get_faces(faceset_id=faceset_id_param, limit=limit_param, offset=offset_param)
    if "error" in faces_data:
        print("Error:", faces_data["error"])
    else:
        for face in faces_data:
            face_id = face.get("id_", "N/A")
            name = face.get("name", "N/A")
            print(f"ID: {face_id}, Name: {name}")
    return jsonify({'faces': faces_data})
@app.route("/upload", methods=['POST'])
def upload():
    try:
        image_file = request.files.get("file")
 
        if image_file:
            image_path = "./selectedimage/" + image_file.filename
            print("image_path =",image_path)
            image_file.save(image_path)
            name = request.form.get("name")
            create_face(image_path, name)
            return jsonify({'status': 'success', 'message': 'Face uploaded successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'No file uploaded.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'})
 
 
def create_face(image_path, name):
    faceset_id = '67616902-2903-4c7d-836e-3d4b18dfb6a3'
    project_id = "3581d0ca-2ad2-423d-980e-a5dc681faaea"
 
    endpoint = f"{face_reg_base_url}/{face_reg_version}/faces"
    headers = get_headers()
 
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")
 
    data = {
        "faceset_id": faceset_id,
        "name": name,
        "project_id": project_id,
        "store_enrollment_images":True,
        "duplicate_face_confidence_threshold":0.75,
        "register_on_duplicate":False,
        "base64image_with_landmark": [
            {
                "base64image": image_data
            }
        ]
       
    }
 
    try:
        response = requests.post(endpoint, json=data, headers=headers)
        print("Response Content:", response.content)
        print("Response Status Code:", response.status_code)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

@app.route('/compare', methods=['POST'])
def compare():
    temp_URL = None
    current_timestamp = int(datetime.datetime.now().timestamp() * 1000)
    end_timestamp = current_timestamp + 15000
    start_timestamp = current_timestamp
    start_time = current_timestamp
    length = 6
    content = "ALL"
    #endpoint_id = 122381
    summary = None
    endpoint_id = session.get('endpoint_id')
    print("Endpoint ID in /compare:", endpoint_id)

    isOnline, device_status = send_status_request(endpoint_id)
    if isOnline == False:
        print("Device is offline")
        return jsonify({'status': 'error', 'message': 'Device is offline'})
    
    response_data, requested_id = send_recording_request(length, content, endpoint_id,summary,start_time)
    print("Response Data:", response_data)
    print("Requested ID:", requested_id)
    call_loop = 3
    delay_seconds = 15
    while call_loop > 0:
        result = get_recording_request(requested_id)
        print("Result:", result)
        if "error" in result:
            print("Error:", result["error"])
            return jsonify({'status': 'success', 'message': "Error in fetching recording status"})
        else:
            print(f"Status: {result['Status']}")
            if result['Status'] != 'COMPLETED':
                time.sleep(delay_seconds)
                call_loop -= 1
                continue
            else:
                print(f"Start Time: {result['Start Time']}")
                temp_URL = get_recordings(start_timestamp,end_timestamp)
                video_response = requests.get(temp_URL)
                video_data = video_response.content
                if video_response.status_code == 200:
                    video_data = video_response.content
                    with open(local_file_path, "wb") as video_file:
                        video_file.write(video_data)
                        print(f"Video downloaded and saved as {local_file_path}")
                else:
                    print(f"Failed to download video. Status code: {video_response.status_code}")
        
                frame_count = 0
                cap = cv2.VideoCapture(local_file_path)
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break  
                    frame_count += 1
                    if frame_count == 3:
                        image_filename = os.path.join(output_directory, "first_frame.jpg")
                        cv2.imwrite(image_filename, frame)
                        print(f"Saved the third frame as {image_filename}")
                        break
                cap.release()
                cv2.destroyAllWindows()
                image_filename = os.path.join(output_directory, "first_frame.jpg")
                image = cv2.imread(image_filename)
                left = 130  
                top = 90    
                right = 350  
                bottom = 350
                cropped_image = image[top:bottom, left:right]
                output_filename = os.path.join(output_directory, "cropped_image.jpg")
                cv2.imwrite(output_filename, cropped_image)  
                with open(image_filename, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode("utf-8")
                    
                lookup_request_data = {
                    "faceset_id": '67616902-2903-4c7d-836e-3d4b18dfb6a3',
                    "project_id": "3581d0ca-2ad2-423d-980e-a5dc681faaea",
                    "size": 0,
                    "merge_images_for_lookup": False,
                    "lookup_request_landmarks": [
                        {
                            "face_landmark": [
                                [0]
                            ],
                            "sequence_number": 0,
                            "base64string":  image_data,
                            "embedding_vector": [
                                0
                            ]
                        }
                    ],
                    "lookup_request_faces": [
                        {
                        "sequence_number": 0,
                        "base64string":image_data,
                    }
                    ]
                }
                face_lookup_result = perform_face_lookup(lookup_request_data)
                print("Face Lookup Result:", json.dumps(face_lookup_result, indent=4))        
                face_landmark_lookup_result = perform_face_landmark_lookup(lookup_request_data)
                print("Face Landmark Lookup Result:", json.dumps(face_landmark_lookup_result, indent=4))
        
        
                confidence_threshold = 0.8
        
                if "lookup_results" in face_landmark_lookup_result:
                    lookup_result = face_landmark_lookup_result["lookup_results"][0]
                    confidence_score = lookup_result.get("confidence_score", 0)  
                    if confidence_score > confidence_threshold:
                        print("Face recognized with confidence:", confidence_score)
                        print("Face Token:", lookup_result["best_matched_face_token"])
                        recognized_name = "Unknown"
                        for lookup_result_face in face_lookup_result.get("lookup_results", []):
                            if lookup_result_face.get("best_matched_face_token") == lookup_result["best_matched_face_token"]:
                                recognized = lookup_result_face.get("best_matched_face_token", "Unknown")
                                for face_info in faces_data:
                                    if face_info.get("face_token") == lookup_result["best_matched_face_token"]:
                                        recognized_name = face_info.get("name", "Unknown")
                                        break
                            break                
            
                        print("Recognized Name:", recognized_name)
            
            
                    else:
                        print("Unknown face. Confidence:", confidence_score)
                else:
                    print("No face landmark lookup results.")
            
                if confidence_score > confidence_threshold:
                    message1 = "Driver is authenticated."
                    summary = "driver_verified"
                    response_data, requested_id = send_recording_request(length, content, endpoint_id,summary,start_time)
                    print("Response Data:", response_data)
                    print("Requested ID:", requested_id)
                elif confidence_score == -1:
                    message1 = "Driver is not present in vehicle"
                    summary = ""    
                else:
                    message1 = "Driver is not authenticated."
                    summary = "driver_verification_failed"
                    response_data, requested_id = send_recording_request(length, content, endpoint_id,summary,start_time)
                    print("Response Data:", response_data)
                    print("Requested ID:", requested_id)
            
                return jsonify({'status': 'success', 'message': message1})        
    return jsonify({'status': 'success', 'message': "Error in fetching video"})        
    # if temp_URL is None:
    #     get_recordings(start_timestamp,end_timestamp)
    #     print("@@@@@@@@@@@@@@@@@@@@@@@@@",temp_URL)
    #     if temp_URL is None:
    #         message1 = "device not provide any video"
    #         # return render_template('index1.html', message=message1)
    #         return jsonify({'status': 'success', 'message': message1})
         

if __name__ == '__main__':
    app.run(debug=True)