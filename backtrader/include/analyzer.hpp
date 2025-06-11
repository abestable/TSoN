#pragma once

#include <vector>
#include <string>
#include "strategy.hpp"

class Analyzer {
public:
    Analyzer(const std::vector<Trade>& trades);
    
    // Performance metrics
    double get_total_pnl() const;
    double get_win_rate() const;
    double get_profit_factor() const;
    double get_max_drawdown() const;
    double get_sharpe_ratio() const;
    double get_sortino_ratio() const;
    double get_calmar_ratio() const;
    
    // Trade statistics
    int get_total_trades() const;
    int get_winning_trades() const;
    int get_losing_trades() const;
    double get_avg_win() const;
    double get_avg_loss() const;
    double get_largest_win() const;
    double get_largest_loss() const;
    
    // Time-based analysis
    std::vector<double> get_monthly_returns() const;
    std::vector<double> get_drawdown_series() const;
    
    // Report generation
    void print_report() const;

private:
    std::vector<Trade> trades_;
    std::vector<double> returns_;
    
    void calculate_returns();
    double calculate_volatility() const;
    double calculate_downside_deviation() const;
}; 