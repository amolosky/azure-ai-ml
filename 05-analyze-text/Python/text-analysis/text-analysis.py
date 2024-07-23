from dotenv import load_dotenv
import os
import requests

# Import namespaces
# from azure.cognitiveservices.language.textanalytics import TextAnalyticsClient


def main():
    # This function is the entry point of the text analysis program.
    # It performs various text analysis tasks on each text file in the 'reviews' folder.
   

    try:
        # Get Configuration Settings.
        
        # Create client using endpoint and key
        load_dotenv()
        # REPLACE YOUR VALUES FOR COG_SERVICE_ENDPOINT AND COG_SERVICE_KEY
        cog_endpoint = os.getenv('COG_SERVICE_ENDPOINT')
        cog_key = os.getenv('COG_SERVICE_KEY')

        headers = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': cog_key
        }

        # Analyze each text file in the reviews folder
        reviews_folder = 'reviews'
        for file_name in os.listdir(reviews_folder):
            # Read the file contents
            print('\n-------------\n' + file_name)
            text = open(os.path.join(reviews_folder, file_name), encoding='utf8').read()
            print('\n' + text)

            # Get language
            language_api_url = f"{cog_endpoint}/text/analytics/v3.0/languages"
            response = requests.post(language_api_url, headers=headers, json={"documents": [{"id": "1", "text": text}]}).json()
            language = response["documents"][0]["detectedLanguages"][0]["iso6391Name"]

            # Get sentiment
            sentiment_api_url = f"{cog_endpoint}/text/analytics/v3.0/sentiment"
            response = requests.post(sentiment_api_url, headers=headers, json={"documents": [{"id": "1", "language": language, "text": text}]}).json()
            sentiment = response["documents"][0]["sentiment"]
            print(f"Sentiment: {sentiment}")


            # Get keyPhrases
            key_phrases_api_url = f"{cog_endpoint}/text/analytics/v3.0/keyPhrases"
            response = requests.post(key_phrases_api_url, headers=headers, json={"documents": [{"id": "1", "language": language, "text": text}]}).json()        
            key_phrases = response["documents"][0]["keyPhrases"]
            print(f"Key Phrases: {key_phrases}")

            # Get entities
            entities_api_url = f"{cog_endpoint}/text/analytics/v3.0/entities"
            response = requests.post(entities_api_url, headers=headers, json={"documents": [{"id": "1", "language": language, "text": text}]}).json()
            entities = response["documents"][0]["entities"]
            print(f"Entities: {entities}")


            # Get linked entities
                # Linked entities in Azure Cognitive Services Text Analytics refer to the "Entity Linking" capability. This feature identifies and disambiguates entities found in text to known entities in a knowledge base (like Wikipedia). For each identified entity, the API provides the entity's name, the Wikipedia URL (if available), the Wikipedia ID, and a Bing ID that uniquely identifies the entity. This can be particularly useful for enhancing understanding of text by linking entities to additional information and context.
            linked_entities_api_url = f"{cog_endpoint}/text/analytics/v3.0/entities/linking"
            response = requests.post(linked_entities_api_url, headers=headers, json={"documents": [{"id": "1", "language": language, "text": text}]}).json()
            linked_entities = response["documents"][0]["entities"]
            print(f"Linked Entities: {linked_entities}")




    except Exception as ex:
        print(f"An error occurred: {ex}")
        


if __name__ == "__main__":
    main()