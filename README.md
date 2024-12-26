# ST5-forward-test

The forward testing code for strategy 5 (ST5).

## Overview

This project is designed to forward test the ST5 strategy. In its current state, the project can:

1. Retrieve pair data from a mock API or a live data server (Binance, currently), in parallelized fashion.
2. Draw the lower order zigzag on the data, given the starting date specified in a `.env` file.
3. Draw the higher order zigzag on the data.
4. Find the segments for a list of pairs provided through a CSV file.
5. Log various activities using a customized logging module.
6. Find signals for a list of pairs based on the ST5 strategy.
7. Selectively run in validation mode, which adds extra debug data to the signals, as well as other features useful for debugging.

### Data Retrieval

- The project can use both mock data from an offline cache, or live Binance data. The live data fetching is done in parallel and in bulk to improve
  performance.

### Zigzag-based signal generation

- **Lower Order Zigzag**: The project can draw the lower order zigzag on the pair data. The starting date for this operation is specified in a `.env`
  file.
- **Higher Order Zigzag**: The project can also draw the higher order zigzag on the pair data, based on the previously drawn LO zigzag.
- **Segment finding**: The project can find segments for a list of pairs in which order blocks are detected.
- **Signal finding**: The project can find signals for a list of pairs based on the ST5 strategy.
- **Signal posting and cancelling**: The project can post signals to a Telegram channel.

### Logging

- The project includes a customized logging module that logs various activities and events, aiding in debugging and monitoring.

### Telegram Integration

- The project will eventually connect to a Telegram channel and post crypto signals based on the ST5 strategy.

## Getting Started

### Prerequisites

- Python
- pip

### Installation

1. Clone the repository.
2. Install the required dependencies using pip.

```sh
pip install -r requirements.txt
```

### Running the project

Execute the following command to run the project:

```sh
python main.py
```

### Changelog

#### ver b0.1

- Initial version, pair fetching from mock API, lower order zigzag drawing, higher order zigzag drawing, segment finding, and logging.

#### ver b0.2

- Major update, added finding signals (single loop currently, not perpetually running), posting signals to Telegram channels, validation mode for
  signals
- Replaced the mock API with actual live Binance API, to be replaced with websocket connection to Binance.

#### ver b0.2.1

- Added signal cancellation in the event a new segment is found, or if no runs of the algorithm have been done prior.
- Added parallelized data fetching using concurrency. The data fetching now happens once per main loop, instead of once for every pair, cutting data
  fetching time by almost 75%.
- Added better logging capabilities with tabs and cleaner output.
- Improve error handling with logger outputs for different exceptions.

#### ver b0.2.2

- Extended validation mode. In its current state, enabling validation mode will cause the algorithm to also post positions that have been entered by
  the candles located after the activation threshold. This enables the user to see what positions were potentially missed by running the algorithm
  late, and what positions would have been entered and possibly profitted off of if the algorithm was running in real time.

#### ver b0.2.3

- Extended usabillity wit hruntime arguments for pair list and channel ID, as well as separate starting time lists based on timeframe.
- Added a utility to cancel all pairs given in the `pair_list.csv` file or any other file given through the runtime argument `--pair_list`.
- Added customizable leverage and leverage types through `.env.params`