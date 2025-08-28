from dotenv import load_dotenv, find_dotenv
import os

# print(os.getenv("ENV", ".env"))

load_dotenv(find_dotenv(os.getenv("ENV", ".env"), usecwd=True), override=False)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
PORT = os.getenv("PORT")

print(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

