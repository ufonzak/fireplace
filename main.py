from src.server import app, start

if __name__ == "__main__":
    from waitress import serve

    start()
    serve(app, host="0.0.0.0", port=8080)
