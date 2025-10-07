#!/usr/bin/env python3
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.parse import urlparse
import threading

class Cache:
    def __init__(self):
        self.data = None
        self.timestamp = None
        self.ttl = 3600000  # 1 hour in milliseconds

cache = Cache()

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Handle CORS
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        if self.path == '/api/filings':
            self.handle_filings()
        elif self.path == '/health':
            self.handle_health()
        else:
            self.send_error(404, "Not Found")

    def handle_filings(self):
        try:
            # Check cache first
            current_time = int(time.time() * 1000)  # Convert to milliseconds
            if cache.data and cache.timestamp and (current_time - cache.timestamp < cache.ttl):
                self.wfile.write(json.dumps(cache.data).encode())
                return

            # Fetch from SEC API
            url = 'https://data.sec.gov/submissions/CIK0001067983.json'
            headers = {
                'User-Agent': 'Buffett Portfolio Monitor contact@youremail.com',
                'Accept-Encoding': 'gzip, deflate',
                'Host': 'data.sec.gov'
            }
            
            req = Request(url, headers=headers)
            with urlopen(req) as response:
                data = json.loads(response.read().decode())
            
            filing_data = data['filings']['recent']
            form13f = []
            
            for i in range(len(filing_data['form'])):
                if filing_data['form'][i] in ['13F-HR', '13F-HR/A']:
                    form13f.append({
                        'form': filing_data['form'][i],
                        'filingDate': filing_data['filingDate'][i],
                        'reportDate': filing_data['reportDate'][i],
                        'accessionNumber': filing_data['accessionNumber'][i],
                        'url': f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001067983&type=13F'
                    })
                    if len(form13f) >= 8:
                        break

            result = {
                'companyName': data['name'],
                'cik': data['cik'],
                'filings': form13f,
                'fetchedAt': datetime.now().isoformat()
            }

            # Update cache
            cache.data = result
            cache.timestamp = current_time
            
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            error_response = {
                'error': 'Failed to fetch SEC data',
                'message': str(e)
            }
            self.send_response(500)
            self.wfile.write(json.dumps(error_response).encode())

    def handle_health(self):
        health_data = {
            'status': 'ok',
            'timestamp': datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(health_data).encode())

    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_server():
    server_address = ('', 3001)
    httpd = HTTPServer(server_address, APIHandler)
    print("🚀 Backend API running on port 3001")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
