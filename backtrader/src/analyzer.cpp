#include "analyzer.hpp"
#include <algorithm>
#include <cmath>
#include <numeric>
#include <iomanip>
#include <iostream>

Analyzer::Analyzer(const std::vector<Trade>& trades) : trades_(trades) {
    calculate_returns();
}

void Analyzer::calculate_returns() {
    returns_.clear();
    double cumulative_pnl = 0.0;
    
    for (const auto& trade : trades_) {
        cumulative_pnl += trade.pnl;
        returns_.push_back(trade.pnl);
    }
}

double Analyzer::get_total_pnl() const {
    return std::accumulate(trades_.begin(), trades_.end(), 0.0,
        [](double sum, const Trade& trade) { return sum + trade.pnl; });
}

double Analyzer::get_win_rate() const {
    if (trades_.empty()) return 0.0;
    int winning_trades = std::count_if(trades_.begin(), trades_.end(),
        [](const Trade& trade) { return trade.pnl > 0; });
    return static_cast<double>(winning_trades) / trades_.size();
}

double Analyzer::get_profit_factor() const {
    double gross_profit = 0.0;
    double gross_loss = 0.0;
    
    for (const auto& trade : trades_) {
        if (trade.pnl > 0) {
            gross_profit += trade.pnl;
        } else {
            gross_loss += std::abs(trade.pnl);
        }
    }
    
    return gross_loss == 0.0 ? 0.0 : gross_profit / gross_loss;
}

double Analyzer::get_max_drawdown() const {
    double max_drawdown = 0.0;
    double peak = 0.0;
    double current_value = 0.0;
    
    for (const auto& trade : trades_) {
        current_value += trade.pnl;
        if (current_value > peak) {
            peak = current_value;
        }
        double drawdown = peak - current_value;
        if (drawdown > max_drawdown) {
            max_drawdown = drawdown;
        }
    }
    
    return max_drawdown;
}

double Analyzer::get_sharpe_ratio() const {
    if (returns_.empty()) return 0.0;
    
    double mean_return = std::accumulate(returns_.begin(), returns_.end(), 0.0) / returns_.size();
    double variance = std::accumulate(returns_.begin(), returns_.end(), 0.0,
        [mean_return](double sum, double ret) {
            return sum + std::pow(ret - mean_return, 2);
        }) / returns_.size();
    
    double std_dev = std::sqrt(variance);
    return std_dev == 0.0 ? 0.0 : mean_return / std_dev;
}

double Analyzer::get_sortino_ratio() const {
    if (returns_.empty()) return 0.0;
    
    double mean_return = std::accumulate(returns_.begin(), returns_.end(), 0.0) / returns_.size();
    double downside_dev = calculate_downside_deviation();
    
    return downside_dev == 0.0 ? 0.0 : mean_return / downside_dev;
}

double Analyzer::get_calmar_ratio() const {
    double max_dd = get_max_drawdown();
    return max_dd == 0.0 ? 0.0 : get_total_pnl() / max_dd;
}

int Analyzer::get_total_trades() const {
    return trades_.size();
}

int Analyzer::get_winning_trades() const {
    return std::count_if(trades_.begin(), trades_.end(),
        [](const Trade& trade) { return trade.pnl > 0; });
}

int Analyzer::get_losing_trades() const {
    return std::count_if(trades_.begin(), trades_.end(),
        [](const Trade& trade) { return trade.pnl <= 0; });
}

double Analyzer::get_avg_win() const {
    auto winning_trades = std::count_if(trades_.begin(), trades_.end(),
        [](const Trade& trade) { return trade.pnl > 0; });
    
    if (winning_trades == 0) return 0.0;
    
    double total_win = std::accumulate(trades_.begin(), trades_.end(), 0.0,
        [](double sum, const Trade& trade) {
            return sum + (trade.pnl > 0 ? trade.pnl : 0.0);
        });
    
    return total_win / winning_trades;
}

double Analyzer::get_avg_loss() const {
    auto losing_trades = std::count_if(trades_.begin(), trades_.end(),
        [](const Trade& trade) { return trade.pnl <= 0; });
    
    if (losing_trades == 0) return 0.0;
    
    double total_loss = std::accumulate(trades_.begin(), trades_.end(), 0.0,
        [](double sum, const Trade& trade) {
            return sum + (trade.pnl <= 0 ? std::abs(trade.pnl) : 0.0);
        });
    
    return total_loss / losing_trades;
}

double Analyzer::get_largest_win() const {
    if (trades_.empty()) return 0.0;
    return std::max_element(trades_.begin(), trades_.end(),
        [](const Trade& a, const Trade& b) { return a.pnl < b.pnl; })->pnl;
}

double Analyzer::get_largest_loss() const {
    if (trades_.empty()) return 0.0;
    return std::min_element(trades_.begin(), trades_.end(),
        [](const Trade& a, const Trade& b) { return a.pnl < b.pnl; })->pnl;
}

std::vector<double> Analyzer::get_monthly_returns() const {
    // This is a simplified version - in a real implementation,
    // you would need to parse the timestamps and group by month
    return returns_;
}

std::vector<double> Analyzer::get_drawdown_series() const {
    std::vector<double> drawdowns;
    double peak = 0.0;
    double current_value = 0.0;
    
    for (const auto& trade : trades_) {
        current_value += trade.pnl;
        if (current_value > peak) {
            peak = current_value;
        }
        drawdowns.push_back(peak - current_value);
    }
    
    return drawdowns;
}

double Analyzer::calculate_volatility() const {
    if (returns_.empty()) return 0.0;
    
    double mean_return = std::accumulate(returns_.begin(), returns_.end(), 0.0) / returns_.size();
    double variance = std::accumulate(returns_.begin(), returns_.end(), 0.0,
        [mean_return](double sum, double ret) {
            return sum + std::pow(ret - mean_return, 2);
        }) / returns_.size();
    
    return std::sqrt(variance);
}

double Analyzer::calculate_downside_deviation() const {
    if (returns_.empty()) return 0.0;
    
    double mean_return = std::accumulate(returns_.begin(), returns_.end(), 0.0) / returns_.size();
    double sum_squared_downside = std::accumulate(returns_.begin(), returns_.end(), 0.0,
        [mean_return](double sum, double ret) {
            return sum + (ret < mean_return ? std::pow(ret - mean_return, 2) : 0.0);
        });
    
    return std::sqrt(sum_squared_downside / returns_.size());
}

void Analyzer::print_report() const {
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "\n=== Performance Report ===\n\n";
    std::cout << "Total PnL: " << get_total_pnl() << "\n";
    std::cout << "Total Trades: " << get_total_trades() << "\n";
    std::cout << "Win Rate: " << get_win_rate() * 100 << "%\n";
    std::cout << "Profit Factor: " << get_profit_factor() << "\n";
    std::cout << "Sharpe Ratio: " << get_sharpe_ratio() << "\n";
    std::cout << "Sortino Ratio: " << get_sortino_ratio() << "\n";
    std::cout << "Calmar Ratio: " << get_calmar_ratio() << "\n";
    std::cout << "Max Drawdown: " << get_max_drawdown() << "\n\n";
    
    std::cout << "Winning Trades: " << get_winning_trades() << "\n";
    std::cout << "Losing Trades: " << get_losing_trades() << "\n";
    std::cout << "Average Win: " << get_avg_win() << "\n";
    std::cout << "Average Loss: " << get_avg_loss() << "\n";
    std::cout << "Largest Win: " << get_largest_win() << "\n";
    std::cout << "Largest Loss: " << get_largest_loss() << "\n";
} 