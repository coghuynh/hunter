from dotenv import load_dotenv, find_dotenv
import os


load_dotenv(find_dotenv(".env", usecwd=True), override=False)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
PORT = os.getenv("PORT")

# print(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

