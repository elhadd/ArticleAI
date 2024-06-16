from flask import Flask, request, jsonify
import requests
from goose3 import Goose
from goose3.network import NetworkError
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello from Flask!'

@app.route('/extractnews', methods=['GET'])
def extract_article_route():
    url = request.args.get('q')
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        content = response.text
        article_data = extract_article_from_content(content)
        main_image = extract_main_image_from_content(content)
        article_data['mainImage'] = main_image
        return jsonify(article_data)
    except requests.RequestException as e:
        return jsonify({"error": f"HTTP error: {e}"}), 500
    except NetworkError as e:
        return jsonify({"error": f"Network error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error: {e}"}), 500

def extract_article_from_content(content):
    g = Goose({'browser_user_agent': 'Mozilla', 'parser_class': 'soup'})
    try:
        article = g.extract(raw_html=content)
        result = {
            'title': article.title,
            'metaDescription': article.meta_description,
            'metaKeywords': article.meta_keywords,
            'canonicalLink': article.canonical_link,
            'domain': article.domain,
            'tags': article.tags,
            'links': article.links,
            'videos': article.movies,
            'articleText': article.cleaned_text,
            'entities': article.tags,
            'topImage': {
                'imageSrc': article.top_image.src if article.top_image else "",
                'imageHeight': article.top_image.height if article.top_image else "",
                'imageWidth': article.top_image.width if article.top_image else "",
                'imageExtractionType': article.top_image.extraction_type if article.top_image else "",
                'imageBytes': article.top_image.bytes if article.top_image else ""
            }
        }
        return result
    except Exception as e:
        return {"error": f"Error extracting article: {e}"}

def extract_main_image_from_content(content):
    try:
        soup = BeautifulSoup(content, 'html.parser')

        # Cerca le immagini nei meta tag
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']

        twitter_image = soup.find('meta', name='twitter:image')
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']

        # Cerca un'immagine all'interno di tag specifici (es. <figure>, <article>)
        main_image = soup.find('article').find('img') if soup.find('article') else None
        if main_image and main_image.get('src'):
            return main_image['src']

        main_image = soup.find('figure').find('img') if soup.find('figure') else None
        if main_image and main_image.get('src'):
            return main_image['src']

        # Trova la prima immagine se nessuna delle precedenti è trovata
        main_image = soup.find('img')
        if main_image and main_image.get('src'):
            return main_image['src']

        return ""
    except Exception as e:
        print(f"Error extracting main image: {e}")
        return ""

if __name__ == '__main__':
    app.run(debug=True)
