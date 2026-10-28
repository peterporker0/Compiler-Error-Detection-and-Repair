from repair_model import train_models
if __name__ == "__main__":
 info=train_models()
 print("Training complete."); print("Rows used:",info["rows"])
 print("Error classes:",", ".join(info["errors"])); print("Repair classes:",", ".join(info["repairs"]))
 print("Models saved in ./models/")
