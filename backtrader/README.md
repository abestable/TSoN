# Random Entry Strategy Backtester (C++ Version)

This is a C++ implementation of the random entry strategy backtester, optimized for performance while maintaining the same functionality as the Python version.

## Dependencies

- C++17 compatible compiler
- CMake 3.10 or higher
- Boost libraries (system, filesystem, program_options)
- CSV Parser library
- Make or Ninja build system

## Building

1. Install dependencies:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install build-essential cmake libboost-all-dev

# Install CSV Parser
git clone https://github.com/vincentlaucsb/csv-parser.git
cd csv-parser
mkdir build && cd build
cmake ..
make
sudo make install
```

2. Build the project:

```bash
mkdir build
cd build
cmake ..
make
```

## Usage

The program accepts the same command-line arguments as the Python version:

```bash
./random_entry_cpp [options]

Options:
  -h [ --help ]                 Show help message
  -s [ --symbol ] arg (=BTCUSDT) Trading Pair
  --tp arg (=0.01)              Take Profit (%)
  --sl arg (=0.01)              Stop Loss (%)
  -t [ --timeframe ] arg (=15m) Timeframe
  -c [ --commission ] arg (=0.0005) Commission (%)
  -i [ --initial-cash ] arg (=100000) Initial Cash
  --size-pct arg (=0.1)         Position Size (%)
  --entry-period arg (=10)      Entry Period (bars)
  --max-hold arg (=3000)        Max Hold (bars)
  --trade-type arg (=LONG)      Trade Type (LONG/SHORT/BOTH)
  --num-cpus arg (=1)           Number of CPUs to use
  --use-numba                   Enable Numba (fast compilation)
  --profile                     Enable profiling
```

Example:

```bash
./random_entry_cpp --symbol BTCUSDT --timeframe 1d --tp 0.02 --sl 0.01 --initial-cash 100000
```

## Data Format

The program expects CSV files in the same format as the Python version, located in the `csv` directory with filenames following the pattern: `{symbol}_{timeframe}.csv`

Example: `csv/btcusdt_1d.csv`

The CSV file should have the following columns:
- datetime
- open
- high
- low
- close
- volume

## Performance Comparison

The C++ version is significantly faster than the Python version due to:
1. Native compilation
2. Efficient memory management
3. Optimized data structures
4. No interpreter overhead

## Output

The program generates the same output format as the Python version, including:
- Trade log in CSV format
- Performance metrics
- Execution time
- Detailed statistics

## License

This project is licensed under the MIT License - see the LICENSE file for details. 