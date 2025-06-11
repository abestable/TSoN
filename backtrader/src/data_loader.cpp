#include "data_loader.hpp"
#include <boost/date_time/posix_time/posix_time.hpp>
#include <boost/date_time/gregorian/gregorian.hpp>
#include <iostream>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <boost/algorithm/string.hpp>

DataLoader::DataLoader(const std::string& data_dir) : data_dir_(data_dir) {
    if (!boost::filesystem::exists(data_dir_)) {
        throw std::runtime_error("Data directory does not exist: " + data_dir);
    }
}

std::vector<OHLCV> DataLoader::load_data(const std::string& symbol, const std::string& timeframe) {
    std::string filename = symbol + "_" + timeframe + ".csv";
    boost::filesystem::path file_path = data_dir_ / filename;
    
    if (!boost::filesystem::exists(file_path)) {
        throw std::runtime_error("Data file does not exist: " + file_path.string());
    }
    
    return parse_csv(file_path.string());
}

std::vector<std::string> DataLoader::get_available_symbols() const {
    std::vector<std::string> symbols;
    
    for (const auto& entry : boost::filesystem::directory_iterator(data_dir_)) {
        if (entry.path().extension() == ".csv") {
            std::string filename = entry.path().filename().string();
            std::string symbol = filename.substr(0, filename.find("_"));
            symbols.push_back(symbol);
        }
    }
    
    return symbols;
}

std::vector<OHLCV> DataLoader::parse_csv(const std::string& filename) {
    std::vector<OHLCV> data;
    std::ifstream file(filename);
    
    if (!file.is_open()) {
        throw std::runtime_error("Could not open file: " + filename);
    }
    
    std::string line;
    // Skip header
    std::getline(file, line);
    
    while (std::getline(file, line)) {
        std::vector<std::string> fields;
        boost::split(fields, line, boost::is_any_of(","));
        
        if (fields.size() >= 6) {
            OHLCV bar;
            bar.datetime = parse_datetime(fields[0]);
            bar.open = std::stod(fields[1]);
            bar.high = std::stod(fields[2]);
            bar.low = std::stod(fields[3]);
            bar.close = std::stod(fields[4]);
            bar.volume = std::stod(fields[5]);
            data.push_back(bar);
        }
    }
    
    return data;
}

bool DataLoader::load_data() {
    if (!boost::filesystem::exists(filename_)) {
        std::cerr << "File not found: " << filename_ << std::endl;
        return false;
    }
    
    try {
        data_ = parse_csv(filename_);
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error loading data: " << e.what() << std::endl;
        return false;
    }
}

boost::posix_time::ptime DataLoader::get_start_date() const {
    return data_.empty() ? boost::posix_time::ptime() : data_.front().datetime;
}

boost::posix_time::ptime DataLoader::get_end_date() const {
    return data_.empty() ? boost::posix_time::ptime() : data_.back().datetime;
}

double DataLoader::get_duration_days() const {
    if (data_.empty()) return 0.0;
    
    boost::posix_time::time_duration duration = data_.back().datetime - data_.front().datetime;
    return duration.total_seconds() / (24.0 * 3600.0);
}

double DataLoader::get_duration_years() const {
    return get_duration_days() / 365.25;
}

boost::posix_time::ptime DataLoader::parse_datetime(const std::string& datetime_str) {
    try {
        return boost::posix_time::time_from_string(datetime_str);
    } catch (const std::exception& e) {
        throw std::runtime_error("Failed to parse datetime: " + datetime_str);
    }
} 