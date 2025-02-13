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

def set_params(workflow, colorDetail, colorBody, token, whatVase, isCreative, isLAB, seed, SFW=False):
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
                workflow[node]['inputs']['value'] = seed
            if workflow[node]['_meta']['title'] == 'GlobalSeedString':
                # Modify seed string for Workflow 1 to include SFW flag
                workflow[node]['inputs']['value'] = str(seed) + ("SFW" if SFW else "")
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
    (i, workflow_1, workflow_2, api_url_1, api_url_2, api_key, token, 
     colorDetail, colorBody, whatVase, isCreative, isLAB, testWF, combination_id, is_sfw, seed) = args
    
    # Prepare and send request for workflow 1 (with SFW flag)
    wf1 = json.loads(json.dumps(workflow_1))
    wf1 = set_params(wf1, colorDetail, colorBody, token, whatVase, isCreative, isLAB, seed, SFW=is_sfw)
    
    # Prepare and send request for workflow 2 (without SFW flag)
    wf2 = json.loads(json.dumps(workflow_2))
    wf2 = set_params(wf2, colorDetail, colorBody, token, whatVase, isCreative, isLAB, seed, SFW=False)

    start1 = time.time()
    response1 = send_request(wf1, api_url_1, api_key, testWF)
    end1 = time.time()
    elapsed1 = round((end1 - start1), 2)

    start2 = time.time()
    response2 = send_request(wf2, api_url_2, api_key, testWF)
    end2 = time.time()
    elapsed2 = round((end2 - start2), 2)

    return (i, token, colorDetail, colorBody, whatVase, isCreative, 
            response1, response2, elapsed1, elapsed2, combination_id, is_sfw, seed)

def main(input_json_path_1, input_json_path_2, api_url_1, api_url_2, 
         api_key, csv_path, isLAB, testWF, num_images, creative_value=None):
    # Load workflows
    with open(input_json_path_1, "r") as f:
        workflow_1 = json.load(f)
    with open(input_json_path_2, "r") as f:
        workflow_2 = json.load(f)

    tokens = load_tokens_from_csv(csv_path)
    if not tokens:
        print("No tokens found in the CSV file.")
        return

    # Define available vases (excluding vase 3)
    vases = [1, 2, 4]
    creative_options = [1, 2]

    print(f"\nRunning comparison test for {num_images} images")
    print("Parameters:")
    print(f"Workflow 1: {input_json_path_1}")
    print(f"Workflow 2: {input_json_path_2}")
    print(f"CSV token list: {csv_path}")
    print(f"isLAB: {isLAB}")
    print("Available parameters:")
    print(f"- Vases: {len(vases)} (using vases: {', '.join(map(str, vases))})")
    print(f"- Colors: {len(colors)}")
    print(f"- Creative options: {len(creative_options)}")
    print("--------------")

    futures = []
    request_times_1 = []
    request_times_2 = []
    
    overall_start = time.time()

    # Generate random parameter combinations
    with ThreadPoolExecutor(max_workers=20) as executor:
        generated_seeds = {}  # Store seeds for each image
        for i in range(num_images):
            # Randomly select parameters
            vase = random.choice(vases)
            color_detail = random.choice(colors)
            color_body = random.choice(colors)
            creative = creative_value if creative_value is not None else random.choice(creative_options)
            token = random.choice(tokens)
            
            # Generate a seed that will be used for both workflows
            seed = random.randint(0, sys.maxsize)
            generated_seeds[i] = seed
            
            # Always set SFW to True for Workflow 1
            is_sfw = True

            args = (
                i, workflow_1, workflow_2, api_url_1, api_url_2, api_key,
                token, color_detail, color_body, vase, creative,
                isLAB, testWF, i, is_sfw, seed
            )
            futures.append(executor.submit(prepare_and_send_request, args))

        # Process completed futures
        for future in as_completed(futures):
            try:
                (i, token, colorDetail, colorBody, whatVase, isCreative,
                 response1, response2, elapsed1, elapsed2, img_id, is_sfw, seed) = future.result()
                
                request_times_1.append(elapsed1)
                request_times_2.append(elapsed2)
                
                print(f"\nImage {i+1}/{num_images}:")
                print(f"Parameters: Vase: {whatVase}, Detail Color: {colorDetail}, "
                      f"Body Color: {colorBody}, Creative: {isCreative}, Seed: {generated_seeds[i]}")
                print(f"Token: {token}")
                print(f"SFW (Workflow 1): {is_sfw}")
                print(f"Workflow 1 Time: {elapsed1}s")
                print(f"Workflow 2 Time: {elapsed2}s")
                
                # Display images if available
                for workflow_num, response in [(1, response1), (2, response2)]:
                    if "images" in response:
                        for node_id, image_data_list in response["images"].items():
                            for image_data in image_data_list:
                                image = Image.open(io.BytesIO(image_data))
                                image.show()
                                print(f"Displayed image from Workflow {workflow_num}")
                
            except Exception as e:
                print(f"Error in request: {e}")

    # Calculate and print timing statistics
    overall_end = time.time()
    total_time = round((overall_end - overall_start), 2)
    
    print("\nTiming Statistics:")
    print("\nWorkflow 1:")
    print(f"Average request time: {round(sum(request_times_1) / len(request_times_1), 2)}s")
    print(f"Maximum request time: {round(max(request_times_1), 2)}s")
    print(f"Minimum request time: {round(min(request_times_1), 2)}s")
    
    print("\nWorkflow 2:")
    print(f"Average request time: {round(sum(request_times_2) / len(request_times_2), 2)}s")
    print(f"Maximum request time: {round(max(request_times_2), 2)}s")
    print(f"Minimum request time: {round(min(request_times_2), 2)}s")
    
    print(f"\nTotal execution time: {total_time}s")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare two workflows for image generation')
    parser.add_argument('--creative', type=int, choices=[1, 2],
                       help='Specify creative parameter value (1 or 2). If not provided, will be randomly selected.')
    parser.add_argument('--num-images', type=int, default=10,
                       help='Number of images to generate (default: 10)')
    
    args = parser.parse_args()
    
    testWF = False
    
    # Workflow paths
    input_json_path_1 = "JasperAI_Runpod_Final_NewTransferTest_MaskedIPA_API_histogram_SFW.json"
    input_json_path_2 = "JasperAI_Runpod_Final_NewTransferTest_MaskedIPA_API_histogram.json"
    
    # API configurations
    api_url_1 = "https://api.runpod.ai/v2/xcnz6lu0iritsg/runsync"
    api_url_2 = "https://api.runpod.ai/v2/xcnz6lu0iritsg/runsync"
    api_key = "rpa_5RPRABDS0X5QJYSFTVB34BKGYH3AHKJOUQLQJON613y2n1"
    
    # Other configurations
    csv_path = "Wedgwood AI Word Bank_V1_Test.csv"
    isLAB = 1
    
    # Update main function parameters
    def main_wrapper(input_json_path_1, input_json_path_2, api_url_1, api_url_2, 
                    api_key, csv_path, isLAB, testWF, num_images, creative=None):
        global creative_value
        creative_value = creative
        return main(input_json_path_1, input_json_path_2, api_url_1, api_url_2, 
                   api_key, csv_path, isLAB, testWF, num_images, creative_value)
    
    main_wrapper(input_json_path_1, input_json_path_2, api_url_1, api_url_2, 
                api_key, csv_path, isLAB, testWF, args.num_images, args.creative)