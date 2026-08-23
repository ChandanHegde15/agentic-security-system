import pandas as pd
import numpy as np
import requests

def main():
    print("Hello from P008 Python app!")
    data = pd.DataFrame({"a": np.arange(5)})
    print(data)

if __name__ == "__main__":
    main()
