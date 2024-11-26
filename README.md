# ST5-forward-test

The forward testing code for strategy 5 (ST5).

## Overview

This project is designed to forward test the ST5 strategy. In its current state, the project can:

1. Retrieve pair data from a mock API, developed and documented separately.
2. Draw the lower order zigzag on the data, given the starting date specified in a `.env` file.
3. Draw the higher order zigzag on the data.
4. Find the segments for a list of pairs provided through a CSV file.
5. Log various activities using a customized logging module.

## Current Capabilities

### Data Retrieval

- The project can fetch pair data for pairs listed in a `pair_list.csv` file from a mock API. This is useful for testing and development purposes without relying on live, exchanged-based data.

### Zigzag Drawing

- **Lower Order Zigzag**: The project can draw the lower order zigzag on the pair data. The starting date for this operation is specified in a `.env` file.
- **Higher Order Zigzag**: The project can also draw the higher order zigzag on the pair data, based on the previously drawn LO zigzag.
- **Segment finding**: The project can find segments for a list of pairs in which order blocks are detected.

### Logging

- The project includes a customized logging module that logs various activities and events, aiding in debugging and monitoring.

## Future Features

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