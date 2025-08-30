from app import create_app
import os


def main():
    print("Hello from ptu-ai-powered-chatbot!")
    basedir = os.path.abspath(os.path.dirname(__file__))
    app = create_app(basedir)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
