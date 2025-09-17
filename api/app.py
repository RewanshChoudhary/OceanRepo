#!/usr/bin/env python3
"""
Marine Data Integration Platform - REST API
Main Flask application providing unified API access to marine data
"""

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from datetime import datetime
import traceback

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from dotenv import load_dotenv
load_dotenv()

# Import API blueprints
from api.routes.data_ingestion import data_ingestion_bp
from api.routes.species_identification import species_bp
from api.routes.oceanographic import oceanographic_bp
from api.routes.spatial import spatial_bp
from api.routes.search import search_bp
from api.routes.analytics import analytics_bp
from api.routes.metadata import metadata_bp
from api.middleware.auth import auth_bp
# from api.utils.database import init_databases
from api.utils.response import APIResponse

def create_app(config=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'marine-platform-secret-key-2024')
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # CORS configuration for frontend integration
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:8080"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["1000 per hour", "100 per minute"]
    )
    limiter.init_app(app)
    
    # Logging setup
    if not app.debug:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s',
            handlers=[
                logging.FileHandler('logs/api.log'),
                logging.StreamHandler()
            ]
        )
    
    # Initialize databases
    # init_databases()  # Commented out to avoid Flask context issues
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(data_ingestion_bp, url_prefix='/api/ingestion')
    app.register_blueprint(species_bp, url_prefix='/api/species')
    app.register_blueprint(oceanographic_bp, url_prefix='/api/oceanographic')
    app.register_blueprint(spatial_bp, url_prefix='/api/spatial')
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(metadata_bp, url_prefix='/api/metadata')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        """System health check endpoint"""
        try:
            # Simple health check without database connections to avoid hanging
            return APIResponse.success({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0',
                'services': {
                    'api': 'running'
                },
                'message': 'API server is running successfully'
            })
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return APIResponse.error('Health check failed', status_code=503)
    
    # API information endpoint
    @app.route('/api/info')
    def api_info():
        """API information and available endpoints"""
        return APIResponse.success({
            'name': 'Marine Data Integration Platform API',
            'version': '1.0.0',
            'description': 'Unified API for marine research data integration and analysis',
            'endpoints': {
                'authentication': '/api/auth',
                'data_ingestion': '/api/ingestion',
                'species_identification': '/api/species',
                'oceanographic_data': '/api/oceanographic',
                'spatial_analysis': '/api/spatial',
                'search': '/api/search',
                'analytics': '/api/analytics',
                'metadata': '/api/metadata'
            },
            'documentation': '/api/docs',
            'health': '/api/health'
        })
    
    # Global error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return APIResponse.error('Bad request', status_code=400)
    
    @app.errorhandler(401)
    def unauthorized(error):
        return APIResponse.error('Unauthorized', status_code=401)
    
    @app.errorhandler(404)
    def not_found(error):
        return APIResponse.error('Resource not found', status_code=404)
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return APIResponse.error('Internal server error', status_code=500)
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle unexpected exceptions"""
        app.logger.error(f"Unhandled exception: {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return APIResponse.error('An unexpected error occurred', status_code=500)
    
    # Request logging middleware
    @app.before_request
    def log_request_info():
        if app.debug:
            app.logger.info(f"Request: {request.method} {request.url}")
            try:
                if request.is_json and request.get_json(silent=True):
                    app.logger.debug(f"Request body: {request.get_json()}")
            except Exception:
                pass  # Ignore JSON parsing errors in logging
    
    @app.after_request
    def log_response_info(response):
        if app.debug:
            app.logger.info(f"Response: {response.status}")
        return response
    
    return app

def main():
    """Run the Flask development server"""
    app = create_app()
    
    # Get configuration from environment
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('API_DEBUG', 'True').lower() == 'true'
    
    print(f"""
🌊 Marine Data Integration Platform API
{'=' * 50}
Starting API server...
Host: {host}
Port: {port}
Debug: {debug}
Environment: {'development' if debug else 'production'}

Available endpoints:
- Health Check: http://{host}:{port}/api/health
- API Info: http://{host}:{port}/api/info
- Documentation: http://{host}:{port}/api/docs

Press Ctrl+C to stop the server
{'=' * 50}
    """)
    
    try:
        app.run(host=host, port=port, debug=debug, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down API server...")
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()