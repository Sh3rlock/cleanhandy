#!/usr/bin/env python
"""
Minimal WSGI application for testing
"""

def application(environ, start_response):
    """Simple WSGI application that always returns a 200 OK"""
    status = '200 OK'
    headers = [('Content-Type', 'application/json')]
    
    response_body = b'{"status": "healthy", "message": "CleanHandy API is running"}'
    
    start_response(status, headers)
    return [response_body]

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8000, application)
    print("Serving on port 8000...")
    httpd.serve_forever()
