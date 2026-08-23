import pandas as pd
import numpy as np
import requests
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    data = {"numbers": np.array([1, 2, 3, 4, 5])}
    df = pd.DataFrame(data)
    total = df["numbers"].sum()
    return f"Sum of numbers is: {total}"

if __name__ == "__main__":
    app.run(debug=True)
