import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']
    host = os.getenv('FLASK_HOST', '0.0.0.0')  # Bind to all interfaces for Docker
    port = int(os.getenv('FLASK_PORT', 5000))
    
    app.run(
        debug=debug,
        host=host,
        port=port,
        threaded=True
    )
