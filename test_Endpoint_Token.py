import json
import requests
import random
import sys
from PIL import Image
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import product

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
    seed = random.randint(0, sys.maxsize)
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
                workflow[node]['inputs']['value'] = str(seed)
    return workflow

def send_request(workflow, api_url, api_key, testWF):
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

def prepare_and_send_request(args):
    (i, original_workflow, api_url, api_key, token, whatVase, isCreative, 
     isLAB, testWF, combination_id) = args
    
    # Randomly select colors for each request
    colorDetail = random.choice(colors)
    colorBody = random.choice(colors)
    
    workflow = json.loads(json.dumps(original_workflow))
    workflow = set_params(workflow, colorDetail, colorBody, token, whatVase, isCreative, isLAB)

    start = time.time()
    response = send_request(workflow, api_url, api_key, testWF)
    end = time.time()
    elapsed = round((end - start), 2)

    return (i, token, colorDetail, colorBody, whatVase, isCreative, 
            response, elapsed, combination_id)

def main(input_json_path, api_url, api_key, csv_path, isLAB, testWF, requests_per_combination, specific_token=None, specific_vases=None):
    # Load workflow and tokens
    with open(input_json_path, "r") as f:
        original_workflow = json.load(f)

    all_tokens = load_tokens_from_csv(csv_path)
    if not all_tokens:
        print("No tokens found in the CSV file.")
        return
        
    # If specific token is provided, verify it exists in the CSV
    if specific_token:
        if specific_token not in all_tokens:
            print(f"Error: Token '{specific_token}' not found in the CSV file.")
            return
        tokens = [specific_token]
        print(f"Testing specific token: {specific_token}")
    else:
        tokens = all_tokens

    # Parameters for combinations
    all_vases = [1, 2, 3, 4]
    creative_options = [1, 2]
    
    # Handle specific vase selection
    if specific_vases:
        invalid_vases = [v for v in specific_vases if v not in all_vases]
        if invalid_vases:
            print(f"Error: Invalid vase types: {invalid_vases}. Must be 1, 2, 3, or 4.")
            return
        vases = specific_vases
        print(f"Testing specific vase types: {vases}")
    else:
        vases = all_vases
    
    # Calculate statistics
    num_tokens = len(tokens)
    combinations_per_token = len(vases) * len(creative_options)
    total_combinations = num_tokens * combinations_per_token
    total_requests = total_combinations * requests_per_combination

    print("Parameters:")
    print(f"CSV token list: {csv_path}")
    print(f"Number of tokens: {num_tokens}")
    print(f"isLAB: {isLAB}")
    print(f"Combinations per token:")
    print(f"- Vases: {len(vases)}")
    print(f"- Creative options: {len(creative_options)}")
    print(f"Total combinations per token: {combinations_per_token}")
    print(f"Total unique combinations: {total_combinations}")
    print(f"Requests per combination: {requests_per_combination}")
    print(f"Total requests to be made: {total_requests}")
    print("--------------")

    futures = []
    request_times = []
    results_by_token = {}
    
    # Record the start time
    overall_start = time.time()

    # Use a ThreadPoolExecutor to run requests in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:
        combination_id = 0
        for token in tokens:
            results_by_token[token] = {
                'times': [],
                'successes': 0,
                'failures': 0
            }
            
            # For each token, test all vase and creative combinations
            for vase, creative in product(vases, creative_options):
                for req_num in range(requests_per_combination):
                    args = (
                        len(futures), original_workflow, api_url, api_key, 
                        token, vase, creative, isLAB, testWF, combination_id
                    )
                    futures.append(executor.submit(prepare_and_send_request, args))
                combination_id += 1

        # Process completed futures
        for future in as_completed(futures):
            try:
                (i, token, colorDetail, colorBody, whatVase, isCreative, 
                 response, elapsed, comb_id) = future.result()
                
                # Store results
                results_by_token[token]['times'].append(elapsed)
                results_by_token[token]['successes'] += 1
                request_times.append(elapsed)
                
                print(f"\nRequest {i+1}/{total_requests} (Combination {comb_id+1}/{total_combinations}):")
                print(f"Token: {token}")
                print(f"Vase: {whatVase}, Creative: {isCreative}")
                print(f"Colors - Detail: {colorDetail}, Body: {colorBody}")
                print(f"Time: {elapsed}s")
                
                # If the response contains image data
                if "images" in response:
                    for node_id, image_data_list in response["images"].items():
                        for image_data in image_data_list:
                            image = Image.open(io.BytesIO(image_data))
                            image.show()
                            
            except Exception as e:
                print(f"Error in request: {e}")
                results_by_token[token]['failures'] += 1

    # Calculate and print timing statistics
    overall_end = time.time()
    total_time = round((overall_end - overall_start), 2)
    avg_time = round(sum(request_times) / len(request_times), 2)
    max_time = round(max(request_times), 2)
    min_time = round(min(request_times), 2)

    print("\nOverall Statistics:")
    print(f"Total time: {total_time}s")
    print(f"Average request time: {avg_time}s")
    print(f"Maximum request time: {max_time}s")
    print(f"Minimum request time: {min_time}s")

    print("\nPer-Token Statistics:")
    for token in tokens:
        token_times = results_by_token[token]['times']
        if token_times:
            token_avg = round(sum(token_times) / len(token_times), 2)
            token_max = round(max(token_times), 2)
            token_min = round(min(token_times), 2)
            success_rate = round(results_by_token[token]['successes'] / 
                               (results_by_token[token]['successes'] + 
                                results_by_token[token]['failures']) * 100, 2)
            
            print(f"\nToken: {token}")
            print(f"Success rate: {success_rate}%")
            print(f"Average time: {token_avg}s")
            print(f"Max time: {token_max}s")
            print(f"Min time: {token_min}s")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests for Wedgwood AI API')
    parser.add_argument('--token', type=str, help='Specific token to test (optional)')
    parser.add_argument('--vases', type=int, nargs='+', choices=[1, 2, 3, 4], 
                        help='Specific vase types to test (optional, can specify multiple e.g., --vases 1 2 4)')
    parser.add_argument('--requests', type=int, default=25, help='Number of requests per combination (default: 25)')
    
    args = parser.parse_args()
    
    testWF = False
    input_json_path = "JasperAI_Runpod_Final_ColorTest_New_API_V2.json"
    #input_json_path = "JasperAI_Runpod_Final_Test_API.json"
    csv_path = "Wedgwood AI Word Bank_V1_Test.csv"
    api_url = "https://api.runpod.ai/v2/ghpeoonf1l7yqb/runsync"
    api_key = "rpa_5RPRABDS0X5QJYSFTVB34BKGYH3AHKJOUQLQJON613y2n1"
    
    isLAB = 1
    
    main(input_json_path, api_url, api_key, csv_path, isLAB, testWF, 
         args.requests, args.token, args.vases)