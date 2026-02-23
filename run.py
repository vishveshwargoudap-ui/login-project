import os
from app.extensions import db
from app import create_app
db.create_all()
app = create_app()

if __name__ == "__main__":
    port=int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0",port=port)