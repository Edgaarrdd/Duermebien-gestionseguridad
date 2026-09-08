import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # En desarrollo local escucha en 127.0.0.1
    # En producción se ejecuta mediante Gunicorn y se conecta por Nginx
    app.run(host="0.0.0.0", port=port, debug=False)
