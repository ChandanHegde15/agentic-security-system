import pandas as pd

# Note: "reqeusts" is listed in requirements.txt but is not imported here,
# since it is a misspelled package name used for testing purposes.

def main():
    df = pd.DataFrame({"values": [1, 2, 3, 4, 5]})
    print("Sum:", df["values"].sum())
    print("Mean:", df["values"].mean())

if __name__ == "__main__":
    main()
