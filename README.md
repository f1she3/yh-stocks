# yh-stocks

## Quickstart
1. Install [Python poetry](https://python-poetry.org/docs/)
2. Install dependencies:<br>
  `poetry install`
3. Start the script:<br>
  `poetry run ./src/main.py`

## Credits
* [ranaroussi](https://github.com/ranaroussi) for his [yfinance](https://github.com/ranaroussi/yfinance) library
* [portfolioplus](https://github.com/portfolioplus) for their [pytickersymbols](https://github.com/portfolioplus/pytickersymbols) library

## Todo
* [x] Add ROI
* [ ] Use [yf.download](https://aroussi.com/post/python-yahoo-finance) for multi-threaded bulk downloading
* [ ] Add a column for every year (maybe create a new dataframe for every stock)
* [x] Implement nice CLI interface ([Rich](https://github.com/Textualize/rich) for example)
