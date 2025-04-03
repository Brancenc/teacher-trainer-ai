import json
import os
import time
from typing import List, Dict, Any
import requests
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaFineTuner:
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize the Ollama fine-tuner.
        
        Args:
            base_url: The URL of the Ollama server
        """
        self.base_url = base_url
        self.model_name = "llama3"  # Base model to use
        
    def check_server(self) -> bool:
        """Check if the Ollama server is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
            
    def prepare_training_data(self, data_path: str) -> List[Dict[str, str]]:
        """Prepare training data in Ollama's format.
        
        Args:
            data_path: Path to the JSONL file containing training data
            
        Returns:
            List of training examples in Ollama's format
        """
        training_data = []
        # Get the absolute path to the data file
        abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', data_path))
        with open(abs_path, 'r') as f:
            for line in f:
                example = json.loads(line)
                # Extract dialogue pairs
                dialogue = example.get("dialogue", [])
                for i in range(0, len(dialogue)-1, 2):
                    if i+1 < len(dialogue):
                        student_msg = dialogue[i]
                        teacher_msg = dialogue[i+1]
                        # Convert to Ollama's format
                        training_data.append({
                            "prompt": student_msg["content"],
                            "response": teacher_msg["content"]
                        })
        return training_data
        
    def create_model(self, model_name: str = "llama3-finetuned") -> bool:
        """Create a new model based on the base model.
        
        Args:
            model_name: Name for the new model
            
        Returns:
            True if successful, False otherwise
        """
        if not self.check_server():
            raise ConnectionError("Ollama server is not running")
            
        try:
            # First, check if the model exists
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            
            if any(model["name"] == model_name for model in models):
                logger.info(f"Model {model_name} already exists")
                return True
                
            # Create the model
            response = requests.post(
                f"{self.base_url}/api/create",
                json={
                    "name": model_name,
                    "model": self.model_name
                }
            )
            response.raise_for_status()
            logger.info(f"Created model {model_name}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating model: {e}")
            return False
            
    def train_model(self, model_name: str, training_data: List[Dict[str, str]]) -> bool:
        """Train the model with the provided data.
        
        Args:
            model_name: Name of the model to train
            training_data: List of training examples
            
        Returns:
            True if successful, False otherwise
        """
        if not self.check_server():
            raise ConnectionError("Ollama server is not running")
            
        try:
            for example in tqdm(training_data, desc="Training model"):
                # Use the chat API for training
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": "You are a helpful teaching assistant. Respond to student questions in a clear and educational manner."},
                            {"role": "user", "content": example["prompt"]},
                            {"role": "assistant", "content": example["response"]}
                        ]
                    }
                )
                response.raise_for_status()
                
            logger.info("Training completed successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during training: {e}")
            return False
                
    def evaluate_model(self, model_name: str, test_data: List[Dict[str, str]]) -> Dict[str, float]:
        """Evaluate the model on test data.
        
        Args:
            model_name: Name of the model to evaluate
            test_data: List of test examples
            
        Returns:
            Dictionary of evaluation metrics
        """
        results = {
            "correct": 0,
            "total": len(test_data),
            "avg_response_time": 0
        }
        
        total_time = 0
        
        for example in tqdm(test_data, desc="Evaluating model"):
            start_time = time.time()
            try:
                # Use the chat API for evaluation
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": "You are a helpful teaching assistant. Respond to student questions in a clear and educational manner."},
                            {"role": "user", "content": example["prompt"]}
                        ]
                    }
                )
                response.raise_for_status()
                generated_response = response.json()["message"]["content"]
                
                # Simple evaluation: check if the answer contains key words
                # This is a basic metric - you might want to implement more sophisticated evaluation
                if any(keyword in generated_response.lower() 
                      for keyword in example["response"].lower().split()):
                    results["correct"] += 1
                    
                total_time += time.time() - start_time
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error during evaluation: {e}")
                continue
                
        results["accuracy"] = results["correct"] / results["total"]
        results["avg_response_time"] = total_time / results["total"]
        
        return results

def main():
    # Initialize the fine-tuner
    fine_tuner = OllamaFineTuner()
    
    # Check if Ollama server is running
    if not fine_tuner.check_server():
        logger.error("Ollama server is not running. Please start it first.")
        return
        
    # Prepare training data
    training_data = fine_tuner.prepare_training_data("data/teacher_student_dialogues.jsonl")
    logger.info(f"Prepared {len(training_data)} training examples")
    
    # Create and train the model
    try:
        model_name = "llama3-finetuned"
        if fine_tuner.create_model(model_name):
            if fine_tuner.train_model(model_name, training_data):
                # Evaluate the model
                test_data = fine_tuner.prepare_training_data("data/small_edu_qa.jsonl")
                results = fine_tuner.evaluate_model(model_name, test_data)
                
                logger.info("Evaluation Results:")
                logger.info(f"Accuracy: {results['accuracy']:.2%}")
                logger.info(f"Average Response Time: {results['avg_response_time']:.2f} seconds")
            else:
                logger.error("Training failed")
        else:
            logger.error("Model creation failed")
        
    except Exception as e:
        logger.error(f"Error during process: {e}")

if __name__ == "__main__":
    main() 