import json
import requests
import random
import sys
from PIL import Image
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import product

# List of color codes (keeping your original colors)
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
    '8761788',    # POWDER_BLUE
    '15526887',   # OFF_WHITE
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
    # Your existing set_params function remains unchanged
    for node in workflow:
        seed = random.randint(0, sys.maxsize)
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
                workflow[node]['inputs']['value'] = seed
            if workflow[node]['_meta']['title'] == 'GlobalSeedString':
                workflow[node]['inputs']['value'] = str(seed)
    return workflow

def send_request(workflow, api_url, api_key, testWF):
    # Your existing send_request function remains unchanged
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
    # Your existing load_tokens_from_csv function remains unchanged
    tokens = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        for line in f:
            token = line.strip()
            if token:
                tokens.append(token)
    return tokens

def prepare_and_send_request(args):
    # Your existing prepare_and_send_request function remains unchanged
    (i, original_workflow, api_url, api_key, token, colorDetail, colorBody, 
     whatVase, isCreative, isLAB, testWF, combination_id) = args
    
    workflow = json.loads(json.dumps(original_workflow))
    workflow = set_params(workflow, colorDetail, colorBody, token, whatVase, isCreative, isLAB)

    start = time.time()
    response = send_request(workflow, api_url, api_key, testWF)
    end = time.time()
    elapsed = round((end - start), 2)

    return (i, token, colorDetail, colorBody, whatVase, isCreative, 
            response, elapsed, combination_id)

def main(input_json_path, api_url, api_key, csv_path, isLAB, testWF, requests_per_combination, specific_vase=None, specific_creative=None):
    # Load workflow and tokens
    with open(input_json_path, "r") as f:
        original_workflow = json.load(f)

    tokens = load_tokens_from_csv(csv_path)
    if not tokens:
        print("No tokens found in the CSV file.")
        return

    # Generate combinations based on whether specific vase and/or creative options are selected
    if specific_creative is None:
        creative_options = [1, 2]
        creative_mode = "all creative options"
    else:
        creative_options = [specific_creative]
        creative_mode = f"creative option {specific_creative}"

    if specific_vase is None:
        vases = [1, 2, 3, 4]
        vase_mode = "all vases"
    else:
        vases = [specific_vase]
        vase_mode = f"vase type {specific_vase}"
        
    mode = f"{vase_mode}, {creative_mode}"
    
    total_combinations = len(vases) * len(colors) * len(colors) * len(creative_options)
    total_requests = total_combinations * requests_per_combination

    print(f"\nRunning test for {mode}")
    print("Parameters:")
    print(f"CSV token list: {csv_path}")
    print(f"isLAB: {isLAB}")
    print(f"Combinations per parameter:")
    print(f"- Vases: {len(vases)} {'(specific vase)' if specific_vase else '(all vases)'}")
    print(f"- Colors (detail): {len(colors)}")
    print(f"- Colors (body): {len(colors)}")
    print(f"- Creative options: {len(creative_options)} {'(specific option)' if specific_creative else '(all options)'}")
    print(f"Total unique combinations: {total_combinations}")
    print(f"Requests per combination: {requests_per_combination}")
    print(f"Total requests to be made: {total_requests}")
    print("--------------")

    futures = []
    request_times = []
    
    # Record the start time
    overall_start = time.time()

    # Create all combinations
    combinations = list(product(vases, colors, colors, creative_options))

    # Use a ThreadPoolExecutor to run requests in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:
        combination_id = 0
        for vase, color_detail, color_body, creative in combinations:
            for req_num in range(requests_per_combination):
                token = random.choice(tokens)
                args = (
                    len(futures), original_workflow, api_url, api_key, 
                    token, color_detail, color_body, vase, creative, 
                    isLAB, testWF, combination_id
                )
                futures.append(executor.submit(prepare_and_send_request, args))
            combination_id += 1

        # Process completed futures
        for future in as_completed(futures):
            try:
                (i, token, colorDetail, colorBody, whatVase, isCreative, 
                 response, elapsed, comb_id) = future.result()
                
                request_times.append(elapsed)
                print(f"\nRequest {i+1}/{total_requests} (Combination {comb_id+1}/{total_combinations}):")
                print(f"Vase: {whatVase}, Detail Color: {colorDetail}, Body Color: {colorBody}, Creative: {isCreative}")
                print(f"Token: {token}")
                print(f"Time: {elapsed}s")
                
                # If the response contains image data
                if "images" in response:
                    for node_id, image_data_list in response["images"].items():
                        for image_data in image_data_list:
                            image = Image.open(io.BytesIO(image_data))
                            image.show()
                            
            except Exception as e:
                print(f"Error in request: {e}")

    # Calculate and print timing statistics
    overall_end = time.time()
    total_time = round((overall_end - overall_start), 2)
    avg_time = round(sum(request_times) / len(request_times), 2)
    max_time = round(max(request_times), 2)
    min_time = round(min(request_times), 2)

    print("\nTiming Statistics:")
    print(f"Total time: {total_time}s")
    print(f"Average request time: {avg_time}s")
    print(f"Maximum request time: {max_time}s")
    print(f"Minimum request time: {min_time}s")

if __name__ == "__main__":
    testWF = False
    #input_json_path = "JasperAI_Runpod_Final_Test_API.json"
    input_json_path = "JasperAI_Runpod_Final_ColorTest_New_API_V2.json"
    csv_path = "Wedgwood AI Word Bank_V1_Test.csv"
    api_url = "https://api.runpod.ai/v2/ghpeoonf1l7yqb/runsync"
    api_key = "rpa_5RPRABDS0X5QJYSFTVB34BKGYH3AHKJOUQLQJON613y2n1"
    
    isLAB = 1
    requests_per_combination = 1  # Number of requests for each unique combination
    
    # Add command line argument parsing
    import argparse
    
    parser = argparse.ArgumentParser(description='Test endpoint for vase combinations')
    parser.add_argument('--vase', type=int, choices=[1, 2, 3, 4], 
                       help='Specific vase type to test (1-4). If not provided, tests all vases.')
    parser.add_argument('--creative', type=int, choices=[1, 2],
                       help='Specific creative option to test (1-2). If not provided, tests all options.')
    
    args = parser.parse_args()
    
    # Run the main function with the specified vase type and creative option (if any)
    main(input_json_path, api_url, api_key, csv_path, isLAB, testWF, 
         requests_per_combination, specific_vase=args.vase, specific_creative=args.creative)