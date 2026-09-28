from database import engine, Base
from models import Conversation, Message

Base.metadata.create_all(bind=engine)

print("Database created successfully.")