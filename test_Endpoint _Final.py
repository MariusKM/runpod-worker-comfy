import json
import requests
import random
import sys
from PIL import Image
import io
import time

# Function to set parameters in the workflow JSON
def set_params(workflow, colorDetail, colorBody, token, whatVase,isCreative,isLAB):
    for node in workflow:
        if node == '552':
            workflow[node]['inputs']['value'] = whatVase
            print("Set whatVase")
        if node == '618':
            workflow[node]['inputs']['value'] = isCreative
            print("Set isCreative")
        if node == '624':
            workflow[node]['inputs']['value'] = isLAB
            print("Set isLAB")
        if '_meta' in workflow[node]:
            if workflow[node]['_meta']['title'] == 'ColorInputDetails':
                workflow[node]['inputs']['value'] = colorDetail
                print("Set ColorInputDetails")
            if workflow[node]['_meta']['title'] == 'ColorInputBody':
                workflow[node]['inputs']['value'] = colorBody
                print("Set ColorInputBody")
            if workflow[node]['_meta']['title'] == 'PromptTokenInput':
                workflow[node]['inputs']['value'] = token
                print("Set PromptTokenInput")
            if workflow[node]['_meta']['title'] == 'GlobalSeed':
                workflow[node]['inputs']['value'] = random.randint(0, sys.maxsize)
                print("Set GlobalSeed")
    return workflow

# Function to send a request to the Runpod API endpoint
def send_request(workflow, api_url, api_key,testWF):
    # Create the request payload
    if testWF:
        request_payload = workflow
    else :
         request_payload = {
        "input": {
            "workflow": workflow,
            "images": []
            
        }
    }
   
    # Add headers
    headers = {
        "accept": "application/json",
        "authorization": f"{api_key}",
        "content-type": "application/json"
    }
    try:
        # Send the POST request
        response = requests.post(api_url, headers=headers, json=request_payload)
        response.raise_for_status()
        print("Request sent successfully.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None

# Main script
def main(input_json_path, api_url, api_key, colorDetail, colorBody, token,whatVase,isCreative,isLAB, testWF):
    # Load the input JSON file
    start = time.time()
    with open(input_json_path, "r") as f:
        workflow = json.load(f)

    # Modify the workflow parameters
    if not testWF:
        workflow = set_params(workflow, colorDetail, colorBody, token,whatVase,isCreative,isLAB)

    # Send the modified workflow to the Runpod API
    response = send_request(workflow, api_url, api_key, testWF)

    # Process the response
    if response:
        end = time.time()
        timespent = round((end - start), 2)
        print("Response received:")
        print(json.dumps(response, indent=2))
        print(f"Time spent: {timespent}s.")

        # If the response contains image data
        if "images" in response:
            for node_id, image_data_list in response["images"].items():
                for image_data in image_data_list:
                    image = Image.open(io.BytesIO(image_data))
                    image.show()
 

if __name__ == "__main__":
    # Input file and API details
    testWF = False
    if testWF :
        input_json_path = "test_input.json"
    else:
        input_json_path = "JasperAI_Runpod_Final_API.json"  # Replace with your JSON file path
    #input_json_path = "JasperAI_AWS_Endpoint_API.json"  # Replace with your JSON file path
    api_url = "https://api.runpod.ai/v2/ghpeoonf1l7yqb/runsync" # Replace with your Runpod API endpoint URL
    api_key = "rpa_5RPRABDS0X5QJYSFTVB34BKGYH3AHKJOUQLQJON613y2n1"  # Replace with your API key

    # Parameters to set
    colorDetail = "5005441"  # Replace with your desired value
    colorBody = "12227444"   # Replace with your desired value
    token = "Car"           # Replace with your desired value
    whatVase =3
    isCreative =1
    isLAB =1

    # Run the main script
    main(input_json_path, api_url, api_key, colorDetail, colorBody, token, whatVase,isCreative,isLAB, testWF)
  

