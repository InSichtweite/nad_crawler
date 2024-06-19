from flask import Flask, request, render_template, redirect, url_for
import subprocess
from urllib.parse import urlparse
from datetime import datetime
import json

nad_crawler_app = Flask(__name__)

@nad_crawler_app.route('/')
def index():
    return render_template('index.html')

@nad_crawler_app.route('/start-scraping', methods=['POST'])
def start_scraping():
    start_url = request.form['start_url']
    parsed_url = urlparse(start_url)
    start_domain = parsed_url.netloc.replace('.', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output_{start_domain}_{timestamp}.json"

    # Run the Scrapy spider
    subprocess.run(["scrapy", "crawl", "crawler01", "-a", f"start_url={start_url}", "-o", output_file])

    return redirect(url_for('show_results', output_file=output_file))

@nad_crawler_app.route('/results')
def show_results():
    output_file = request.args.get('output_file')
    with open(output_file, 'r') as f:
        results = json.load(f)
    return render_template('results.html', results=results)

if __name__ == '__main__':
    nad_crawler_app.run(debug=True)