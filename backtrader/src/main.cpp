#include <iostream>
#include <string>
#include <boost/program_options.hpp>
#include "data_loader.hpp"
#include "strategy.hpp"
#include "analyzer.hpp"

namespace po = boost::program_options;

int main(int argc, char* argv[]) {
    try {
        // Define command line options
        po::options_description desc("Allowed options");
        desc.add_options()
            ("help,h", "Show help message")
            ("data-dir,d", po::value<std::string>()->required(), "Data directory containing CSV files")
            ("symbol,s", po::value<std::string>()->default_value("BTCUSDT"), "Trading symbol")
            ("tp", po::value<double>()->default_value(0.01), "Take Profit (%)")
            ("sl", po::value<double>()->default_value(0.01), "Stop Loss (%)")
            ("timeframe,t", po::value<std::string>()->default_value("1d"), "Timeframe")
            ("commission,c", po::value<double>()->default_value(0.0005), "Commission (%)")
            ("initial-cash,i", po::value<double>()->default_value(100000), "Initial Cash")
            ("size-pct", po::value<double>()->default_value(0.1), "Position Size (%)")
            ("entry-period", po::value<int>()->default_value(10), "Entry Period (bars)")
            ("max-hold", po::value<int>()->default_value(3000), "Max Hold (bars)")
            ("trade-type", po::value<std::string>()->default_value("LONG"), "Trade Type (LONG/SHORT/BOTH)")
            ("num-cpus", po::value<int>()->default_value(1), "Number of CPUs to use")
            ("seed", po::value<unsigned int>(), "Random seed for reproducibility");

        // Parse command line arguments
        po::variables_map vm;
        po::store(po::parse_command_line(argc, argv, desc), vm);

        if (vm.count("help")) {
            std::cout << desc << "\n";
            return 0;
        }

        po::notify(vm);

        // Set random seed if provided
        if (vm.count("seed")) {
            srand(vm["seed"].as<unsigned int>());
        }

        // Load data
        DataLoader loader(vm["data-dir"].as<std::string>());
        std::string symbol = vm["symbol"].as<std::string>();
        std::string timeframe = vm["timeframe"].as<std::string>();
        std::cout << "Loading data for " << symbol << " on " << timeframe << " timeframe...\n";
        auto data = loader.load_data(symbol, timeframe);
        std::cout << "Loaded " << data.size() << " bars\n";

        // Get parameters
        double tp = vm["tp"].as<double>();
        double sl = vm["sl"].as<double>();
        double commission = vm["commission"].as<double>();
        double initial_cash = vm["initial-cash"].as<double>();
        double size_pct = vm["size-pct"].as<double>();
        int entry_period = vm["entry-period"].as<int>();
        int max_hold = vm["max-hold"].as<int>();
        std::string trade_type = vm["trade-type"].as<std::string>();
        int num_cpus = vm["num-cpus"].as<int>();

        // Run strategy (to be updated to accept all params)
        Strategy strategy(symbol, timeframe, tp, sl, commission, initial_cash, size_pct, entry_period, max_hold, trade_type);
        strategy.run(data);

        // Analyze results
        Analyzer analyzer(strategy.get_trades());
        analyzer.print_report();

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }

    return 0;
} 