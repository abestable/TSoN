#pragma once

#include <string>
#include <vector>
#include <memory>
#include <boost/filesystem.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>

struct OHLCV {
    boost::posix_time::ptime datetime;
    double open;
    double high;
    double low;
    double close;
    double volume;
};

class DataLoader {
public:
    DataLoader(const std::string& data_dir);
    std::vector<OHLCV> load_data(const std::string& symbol, const std::string& timeframe);
    std::vector<std::string> get_available_symbols() const;
    bool load_data();
    boost::posix_time::ptime get_start_date() const;
    boost::posix_time::ptime get_end_date() const;
    double get_duration_days() const;
    double get_duration_years() const;

private:
    boost::filesystem::path data_dir_;
    std::string filename_;
    std::vector<OHLCV> data_;
    std::vector<OHLCV> parse_csv(const std::string& file_path);
    boost::posix_time::ptime parse_datetime(const std::string& datetime_str);
}; 