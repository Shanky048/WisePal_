import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

print("--- WisePal AI Model Diagnostic Tool ---")
print("Attempting to configure API key...")

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("ERROR: GOOGLE_API_KEY not found in .env file. Please check your .env file.")
    
    genai.configure(api_key=api_key)
    print("API key configured successfully.")

    print("\nFetching available models that support 'generateContent'...\n")

    available_models = []
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            available_models.append(model.name)

    if not available_models:
        print("CRITICAL ERROR: No models supporting 'generateContent' were found. This indicates an issue with your Google Cloud project setup or API permissions.")
    else:
        print("SUCCESS! Please use one of the following model names in your main.py file:")
        for model_name in available_models:
            print(f"-> {model_name}")

except Exception as e:
    print(f"\nAN ERROR OCCURRED: {e}")
    print("Please double-check your API key and that the Generative Language API is enabled in your Google Cloud project.")

    
