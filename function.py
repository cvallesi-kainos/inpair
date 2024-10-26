import requests
import folium
import os
from google.cloud import storage
from datetime import datetime

def function_handler(request):
    # Read API token from environment variable
    env_variable_name = 'INPOST_API_TOKEN'
    token = os.environ.get(env_variable_name)

    if not token:
        return {
            'statusCode': 500,
            'body': f'Error: {env_variable_name} environment variable not set.'
        }

    # API location and auth
    url = "https://api.inpost.pl/v1/points"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a folium map centered on Poland
    map_center = [52, 19]
    my_map = folium.Map(location=map_center, zoom_start=7)
    
    # Color coding for different air quality indexes from points
    air_quality_index_to_color_code = {
        "VERY_GOOD": "green",
        "GOOD": "lightgreen",
        "SATISFACTORY": "orange",
        "MODERATE": "red",
        "BAD": "darkred",
        "VERY_BAD": "black"
    }

    # Get number of pages with points
    page_count = requests.get(url, headers=headers)
    if page_count.status_code == 200:
        total_pages = page_count.json()["total_pages"]
    else:
        print(page_count.status_code)
        return {
            'statusCode': page_count.status_code,
            'body': f'Error fetching page count: {page_count.text}'
        }
    
    # Go through all the pages to get all the points that report air_index_level (not None)
    for i in range(1, total_pages + 1):
        params = {'page': i}
        print(i)
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            points = response.json()["items"]
            
            for point in points:
                if point["air_index_level"] is not None:
                    color_code = air_quality_index_to_color_code.get(point["air_index_level"], "grey")
                    air_quality_index = point["air_index_level"]
                    folium.Circle(
                        location=[point['location']['latitude'], point['location']['longitude']],
                        radius=750,
                        fill_opacity=0.6,
                        fill_color=color_code,
                        stroke=False,
                        tooltip=air_quality_index
                    ).add_to(my_map)
        else:
            print(response.status_code)
            return {
                'statusCode': response.status_code,
                'body': f'Error fetching points: {response.text}'
            }

    # Add the current date as a text label as the title
    current_date = datetime.now().strftime("%H:%M %d.%m.%Y")
    title_html = f'<h1 style="position:absolute;z-index:100000;left:35vw">Dane pobrano o godzinie {current_date}</h1>'
    my_map.get_root().html.add_child(folium.Element(title_html))
    
    # Save the map as a file in /tmp (required by Google Cloud Functions)
    html_file_path = "/tmp/index.html"
    my_map.save(html_file_path)
    
    # Upload file to Google Cloud Storage
    bucket_name = os.environ.get('GCS_BUCKET_NAME')
    gcs_object_key = "index.html"
    content_type = "text/html"

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(gcs_object_key)

        # Upload the file
        blob.upload_from_filename(html_file_path, content_type=content_type)
        print(f"HTML file uploaded to Google Cloud Storage: gs://{bucket_name}/{gcs_object_key}")
    except FileNotFoundError:
        return {
            'statusCode': 500,
            'body': f'The file {gcs_object_key} was not found.'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'An error occurred: {str(e)}'
        }

    return {
        'statusCode': 200,
        'body': 'HTML file uploaded to Google Cloud Storage successfully.'
    }
