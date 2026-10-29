# Data sources and recovery

The two sources remain separate. Matching ID values would not establish that they describe the same people. No joins are performed between the sources.

## Financial source

- Publisher: Anand Kumar, Kaggle account `manandkumar`.
- [Original dataset page](https://www.kaggle.com/datasets/manandkumar/gen-z-money-spending-dataset).
- [Official metadata](https://www.kaggle.com/api/v1/datasets/view/manandkumar/gen-z-money-spending-dataset).
- Version 1, initial release and last update: `2025-01-31T12:27:43.5Z`, before March 2025.
- File: `raw/genz_money_spends.csv`, 1,700 records and 15 columns, including ID and age.
- CSV SHA-256: `7f11ed0fd2e95de43687d84ad6ee7d575b0c61f7a06d4522bffe15fb6c8dab41`.
- [Pinned version 1 ZIP](https://www.kaggle.com/api/v1/datasets/download/manandkumar/gen-z-money-spending-dataset?datasetVersionNumber=1).
- License reported by Kaggle: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/), allowing copying, modification and redistribution. This statement applies to the financial dataset, not automatically to other files.

The financial CSV is included under the publisher's CC0 designation. Its structure, age range and two core calculations match the course presentation. The original course file and code were lost, so byte-for-byte identity cannot be established.

The source does not identify a survey organization, recruitment process, collection date, geography, amount period, or data-generation method. It does not say whether the records are observed or synthetic. Treat origin as unverified. The upload date is not a survey date. USD is in the original headers; a monthly or annual period is not documented. Comparing spending and income assumes compatible periods and is an operational comparison, not evidence of debt or financial distress.

## Shopping source

- Publisher: Sourav Banerjee, Kaggle account `iamsouravbanerjee`.
- [Original dataset page](https://www.kaggle.com/datasets/iamsouravbanerjee/customer-shopping-trends-dataset).
- Version 2, [pinned ZIP](https://www.kaggle.com/api/v1/datasets/download/iamsouravbanerjee/customer-shopping-trends-dataset?datasetVersionNumber=2).
- The publisher explicitly describes this as synthetic data generated with ChatGPT for learning.
- The license field says `Other (specified in description)`; the reviewed description does not clearly grant redistribution. Neither raw shopping CSV is committed.
- Place `shopping_trends_updated.csv` in `data/raw/`, or use `python src/00_download_shopping.py` to fetch the pinned public ZIP.
- Updated CSV SHA-256: `3e05d375388b7f74039bfeefd41405075e0b0643e1d04a77de1ed11cd1e68dd5`.

The updated file has 3,900 records and 18 columns. The other CSV has 19 columns and contains both actual and preferred payment method. In the updated file, `Payment Method` corresponds to `Preferred Payment Method` in the 19-column file. It is interpreted as a preference in this project. Neither variant contains the financial source's income data.

The shopping file is a recovered candidate that fits the presentation's topic and fields, not a verified copy of the lost course file. Age 18-27 is a fixed operational proxy, not a verified birth cohort. No collection year is documented. See the saved claim comparisons for any differences from the course presentation.

## Local files and public aggregates

SQLite databases and row-level processed files are created under `data/processed/` and ignored by Git. Public tables contain group-level aggregates only. Do not copy the original course presentation or other participants' code into this repository.
