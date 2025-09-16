from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, FunctionDeclaration, Tool
from config import PROJECT_ID, LOCATION, MODEL_NAME

# Initialize Vertex AI
aiplatform.init(project=PROJECT_ID, location=LOCATION)

# Model instantiation
MODEL = None
try:
    MODEL = GenerativeModel(MODEL_NAME)
    print("Model instantiated:", MODEL_NAME)
except Exception as e:
    print("Warning: model instantiation at startup failed; will attempt at runtime. Error:", e)

# Crisis detection functions
def handle_crisis_situation():
    return {"action": "crisis_detected"}

def handle_calm_situation():
    return {"action": "calm_detected"}

# Function declarations for crisis detection
crisis_declaration = FunctionDeclaration(
    name="handle_crisis_situation",
    description="Detects explicit expressions of self-harm, suicidal ideation, or other immediate, severe mental health distress.",
    parameters={
        "type": "object",
        "properties": {},
    }
)

calm_declaration = FunctionDeclaration(
    name="handle_calm_situation",
    description="Detects when a user is expressing that they are feeling better or have calmed down.",
    parameters={
        "type": "object",
        "properties": {},
    }
)

tools = Tool(function_declarations=[crisis_declaration, calm_declaration])