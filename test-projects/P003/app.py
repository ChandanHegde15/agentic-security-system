import pandas as pd
import numpy as np

# Note: superfast-ai-99999 is listed in requirements.txt but is not
# imported here, since it is a placeholder/test package name.

def main():
    data = np.array([1, 2, 3, 4, 5])
    df = pd.DataFrame({"values": data})
    print("Sum:", df["values"].sum())
    print("Mean:", df["values"].mean())

if __name__ == "__main__":
    main()
