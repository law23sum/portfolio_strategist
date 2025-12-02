"""
Custom X-Frame-Options middleware that allows API endpoints to be embedded
in iOS app web views while maintaining security for regular web pages.
"""


class CustomXFrameOptionsMiddleware:
    """
    Middleware that sets X-Frame-Options header conditionally:
    - API endpoints: Allows embedding (removes X-Frame-Options header)
    - Regular web pages: DENY (prevents clickjacking)
    
    This middleware is designed to work with iOS apps that use web views
    to display API content. API endpoints don't need X-Frame-Options protection
    since they return JSON data, not HTML that could be clickjacked.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if this is an API endpoint
        path = request.path
        
        # API path patterns that should allow embedding
        # Most API endpoints start with /api/, but some are nested
        api_path_patterns = [
            '/api/',  # Main API prefix (covers /api/auth/, /api/schema/, etc.)
            '/records/api/',  # Records API endpoints
            '/chat/api/',  # Chat API endpoints
            '/stock-analysis/api/',  # Stock analysis API endpoints
            '/dashboard/api/',  # Dashboard API endpoints
            '/pegasus/employees/api/',  # Employee API endpoints
            '/pegasus/tasks/api/',  # Tasks API endpoints
            '/subscriptions/api/',  # Subscription API endpoints
        ]
        
        # Check if the path matches any API pattern
        is_api_endpoint = any(path.startswith(pattern) for pattern in api_path_patterns)
        
        # Also check if it's a JSON response (API responses are typically JSON)
        # This catches any API endpoint that returns JSON, even if path doesn't match
        content_type = response.get('Content-Type', '')
        is_json_response = 'application/json' in content_type.lower()
        
        if is_api_endpoint or is_json_response:
            # For API endpoints, remove X-Frame-Options header to allow embedding
            # This allows iOS app web views to display the content
            if 'X-Frame-Options' in response:
                del response['X-Frame-Options']
        else:
            # For regular web pages, set DENY to prevent clickjacking
            response['X-Frame-Options'] = 'DENY'

        return response

