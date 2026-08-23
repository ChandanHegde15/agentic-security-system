import pandas as pd
import numpy as np
import requests
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    data = {"numbers": np.array([10, 20, 30, 40, 50])}
    df = pd.DataFrame(data)
    average = df["numbers"].mean()
    return f"Average of numbers is: {average}"

if __name__ == "__main__":
    app.run(debug=True)
