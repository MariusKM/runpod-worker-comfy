import json
import requests
import random
import sys
from PIL import Image
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# List of color codes
colors = [
    '3350979',    # INDIGO
    '11212013',   # ELECTRIC_PURPLE
    '65378',      # LIME_GREEN
    '55512',      # TURQUOISE
    '16752128',   # AMBER
    '16765440',   # GOLDEN_YELLOW
    '2916897',    # FOREST_GREEN
    '16600577',   # VERMILION
    '5005441',    # SLATE_BLUE
    '8495811',    # STEEL_BLUE
    '8761788'     # POWDER_BLUE
    '15526887'    # OFF_WHITE
    '7495776',    # DUSTY_ROSE
    '7827809',    # WARM_GRAY
    '14199131',   # GOLDEN_TAN
    '15721872',   # PALE_YELLOW
    '5987425',    # GUNMETAL_GRAY
    '12498350',   # LIGHT_TAUPE
    '10521488',   # MAUVE
    '15321022'    # MISTY_ROSE
]

def set_params(workflow, colorDetail, colorBody, token, whatVase, isCreative, isLAB):
    for node in workflow:
        if node == '552':
            workflow[node]['inputs']['value'] = whatVase
        if node == '618':
            workflow[node]['inputs']['value'] = isCreative
        if node == '624':
            workflow[node]['inputs']['value'] = isLAB

        if '_meta' in workflow[node]:
            if workflow[node]['_meta']['title'] == 'ColorInputDetails':
                workflow[node]['inputs']['value'] = colorDetail
            if workflow[node]['_meta']['title'] == 'ColorInputBody':
                workflow[node]['inputs']['value'] = colorBody
            if workflow[node]['_meta']['title'] == 'PromptTokenInput':
                workflow[node]['inputs']['value'] = token
            if workflow[node]['_meta']['title'] == 'GlobalSeed':
                workflow[node]['inputs']['value'] = random.randint(0, sys.maxsize)
            if workflow[node]['_meta']['title'] == 'GlobalSeedString':
                workflow[node]['inputs']['value'] = str(random.randint(0, sys.maxsize))
                print("Set GlobalSeedString")
    return workflow

def send_request(workflow, api_url, api_key, testWF):
    # Create the request payload
    if testWF:
        request_payload = workflow
    else:
        request_payload = {
            "input": {
                "workflow": workflow,
                "images": []
            }
        }

    headers = {
        "accept": "application/json",
        "authorization": f"{api_key}",
        "content-type": "application/json"
    }

    response = requests.post(api_url, headers=headers, json=request_payload)
    response.raise_for_status()
    return response.json()

def load_tokens_from_csv(csv_path):
    tokens = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        for line in f:
            token = line.strip()
            if token:
                tokens.append(token)
    return tokens

def prepare_and_send_request(i, original_workflow, api_url, api_key, tokens, isLAB, testWF):
    # Each request has its own parameters chosen randomly
    workflow = json.loads(json.dumps(original_workflow))

    colorDetail = random.choice(colors)
    colorBody = random.choice(colors)
    whatVase = 1    # Random integer 1-4
    isCreative = random.choice([1, 2])   # Random 1 or 2
    token = random.choice(tokens)        # Random token from CSV

    # Set parameters
    workflow = set_params(workflow, colorDetail, colorBody, token, whatVase, isCreative, isLAB)

    start = time.time()
    response = send_request(workflow, api_url, api_key, testWF)
    end = time.time()
    elapsed = round((end - start), 2)

    return i, token, colorDetail, colorBody, whatVase, isCreative, response, elapsed

def main(input_json_path, api_url, api_key, csv_path, isLAB, testWF, num_requests):
    # Load workflow and tokens
    with open(input_json_path, "r") as f:
        original_workflow = json.load(f)

    tokens = load_tokens_from_csv(csv_path)
    if not tokens:
        print("No tokens found in the CSV file.")
        return

    print("Parameters:")
    print(f"CSV token list: {csv_path}")
    print(f"isLAB: {isLAB}")
    print(f"Number of requests: {num_requests}")
    print("--------------")

    futures = []
    request_times = []

    # Record the start time before sending any requests
    overall_start = time.time()

    # Use a ThreadPoolExecutor to run requests in parallel
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        for i in range(num_requests):
            futures.append(executor.submit(
                prepare_and_send_request,
                i, original_workflow, api_url, api_key, tokens, isLAB, testWF
            ))

        # Process completed futures as they come in
        for future in as_completed(futures):
            try:
                i, token, colorDetail, colorBody, whatVase, isCreative, response, elapsed = future.result()
                request_times.append(elapsed)
                print(f"\nRequest {i+1}/{num_requests}:")
                print(f"Chosen token: {token}")
                print(f"Chosen colorDetail: {colorDetail}")
                print(f"Chosen colorBody: {colorBody}")
                print(f"Chosen whatVase: {whatVase}")
                print(f"Chosen isCreative: {isCreative}")
                print("Response received:")
                print(json.dumps(response, indent=2))
                print(f"Time spent on request {i+1}: {elapsed}s.")

                # If the response contains image data
                if "images" in response:
                    for node_id, image_data_list in response["images"].items():
                        for image_data in image_data_list:
                            image = Image.open(io.BytesIO(image_data))
                            image.show()
            except Exception as e:
                print(f"Error in request: {e}")

    # After all requests, record the end time and compute total time
    overall_end = time.time()
    total_time = round((overall_end - overall_start), 2)

    # Print the recorded times and total time
    print("\nAll request times:")
    for idx, t in enumerate(request_times, start=1):
        print(f"Request {idx}: {t}s")

    print(f"\nTotal time for all {num_requests} requests: {total_time}s")

if __name__ == "__main__":
    testWF = False
    input_json_path = "JasperAI_Runpod_Final_ColorTest_New_API.json"  # Update this path if needed
    csv_path = "Wedgwood AI Word Bank_V1_Test.csv"           # The CSV file containing tokens
    api_url = "https://api.runpod.ai/v2/ghpeoonf1l7yqb/runsync" # Update if needed
    api_key = "rpa_5RPRABDS0X5QJYSFTVB34BKGYH3AHKJOUQLQJON613y2n1"  # Replace with your actual API key
    
    isLAB = 1
    num_requests = 1  # Number of requests to send

    main(input_json_path, api_url, api_key, csv_path, isLAB, testWF, num_requests)
