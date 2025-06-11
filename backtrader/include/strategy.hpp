#pragma once

#include <vector>
#include <string>
#include <boost/date_time/posix_time/posix_time.hpp>
#include "data_loader.hpp"

struct Trade {
    boost::posix_time::ptime entry_time;
    boost::posix_time::ptime exit_time;
    double entry_price;
    double exit_price;
    double pnl;
    bool is_long;
};

class Strategy {
public:
    Strategy(const std::string& symbol,
             const std::string& timeframe,
             double tp,
             double sl,
             double commission,
             double initial_cash,
             double size_pct,
             int entry_period,
             int max_hold,
             const std::string& trade_type);
    void run(const std::vector<OHLCV>& data);
    const std::vector<Trade>& get_trades() const { return trades_; }
    double get_total_pnl() const;
    double get_win_rate() const;
    double get_profit_factor() const;
    double get_max_drawdown() const;

private:
    std::string symbol_;
    std::string timeframe_;
    std::vector<Trade> trades_;
    double current_position_;
    double entry_price_;
    boost::posix_time::ptime entry_time_;
    double tp_;
    double sl_;
    double commission_;
    double initial_cash_;
    double size_pct_;
    int entry_period_;
    int max_hold_;
    std::string trade_type_;
    double cash_;
    int bar_in_trade_;
    std::string position_type_; // "long" or "short"
    int last_entry_bar_;

    void process_bar(const OHLCV& bar);
    void close_position(const OHLCV& bar, const std::string& exit_reason);
}; 