# 1.  **what is this**
A tool to modify the feature binning results based on other features count or rate.
currently, it supports .csv and .parquet file only.

# 2.  **how to use**
  - python3 grouping.py
  - need to have flask, pyarrow (for reading parquet file) and mongodb installed

# 3.  **need to do**
 1. bugs:
  - can't click data in navigation panel when in the feature display page
 2. user authorization:
  - add user auth function
 3. UI adjustments
 4. add upload data:
  - flask can only take data with a smaller size, how to deal with larger dataset?
 5. add Auto EDA feature
