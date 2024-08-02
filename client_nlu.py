import requests
import json

# Define the base URL of the Flask server
BASE_URL = 'http://127.0.0.1:10096'

# Function to upload the word list to the server
def upload_words(word_list):
    url = f'{BASE_URL}/upload_words'
    payload = {
        'sentences_to_compare': word_list
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print("Word list uploaded successfully.")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response: {response.json()}")
    except Exception as err:
        print(f"Other error occurred: {err}")

# Function to get the best match for a source sentence
def match_sentence(source_sentence):
    url = f'{BASE_URL}/match_sentence'
    payload = {
        'source_sentence': source_sentence
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        print(f"Best match: {result['best_match']}")
        print(f"Score: {result['score']}")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response: {response.json()}")
    except Exception as err:
        print(f"Other error occurred: {err}")

# Example usage
if __name__ == '__main__':
    # Step 1: Upload a list of sentences to compare
    word_list = ["开启wps软件", "关闭wps软件", "打开浏览器"]
    upload_words(word_list)
    
    # Step 2: Match a source sentence against the uploaded list
    source_sentence = "打开wps软件"
    match_sentence(source_sentence)
