#include "strategy.hpp"
#include <random>
#include <algorithm>
#include <cmath>
#include <iostream>

Strategy::Strategy(const std::string& symbol,
                   const std::string& timeframe,
                   double tp,
                   double sl,
                   double commission,
                   double initial_cash,
                   double size_pct,
                   int entry_period,
                   int max_hold,
                   const std::string& trade_type)
    : symbol_(symbol), timeframe_(timeframe),
      tp_(tp), sl_(sl), commission_(commission), initial_cash_(initial_cash),
      size_pct_(size_pct), entry_period_(entry_period), max_hold_(max_hold),
      trade_type_(trade_type), cash_(initial_cash),
      current_position_(0.0), entry_price_(0.0), bar_in_trade_(0), last_entry_bar_(-entry_period), position_type_("") {}

void Strategy::run(const std::vector<OHLCV>& data) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis(0.0, 1.0);
    int bar_idx = 0;
    for (const auto& bar : data) {
        // Gestione posizione aperta
        if (current_position_ != 0.0) {
            bar_in_trade_++;
            double tp_price, sl_price;
            if (position_type_ == "long") {
                tp_price = entry_price_ * (1 + tp_);
                sl_price = entry_price_ * (1 - sl_);
                if (bar.high >= tp_price) {
                    close_position(bar, "TP");
                } else if (bar.low <= sl_price) {
                    close_position(bar, "SL");
                } else if (bar_in_trade_ >= max_hold_) {
                    close_position(bar, "TIME");
                }
            } else if (position_type_ == "short") {
                tp_price = entry_price_ * (1 - tp_);
                sl_price = entry_price_ * (1 + sl_);
                if (bar.low <= tp_price) {
                    close_position(bar, "TP");
                } else if (bar.high >= sl_price) {
                    close_position(bar, "SL");
                } else if (bar_in_trade_ >= max_hold_) {
                    close_position(bar, "TIME");
                }
            }
        }
        // Logica di ingresso random
        if (current_position_ == 0.0 && (bar_idx - last_entry_bar_) >= entry_period_) {
            if (dis(gen) < 0.5) { // 50% probabilità di entrare
                double position_size = cash_ * size_pct_ / bar.close;
                if (position_size >= 0.001) {
                    std::string ttype = trade_type_;
                    if (ttype == "BOTH") {
                        ttype = (dis(gen) < 0.5) ? "LONG" : "SHORT";
                    }
                    if (ttype == "LONG") {
                        current_position_ = position_size;
                        position_type_ = "long";
                    } else if (ttype == "SHORT") {
                        current_position_ = -position_size;
                        position_type_ = "short";
                    }
                    entry_price_ = bar.close;
                    entry_time_ = bar.datetime;
                    bar_in_trade_ = 0;
                    last_entry_bar_ = bar_idx;
                }
            }
        }
        process_bar(bar);
        bar_idx++;
    }
    // Chiudi posizione aperta a fine dati
    if (current_position_ != 0.0 && !data.empty()) {
        close_position(data.back(), "END");
    }
}

void Strategy::process_bar(const OHLCV& bar) {
    // Placeholder per eventuale logica aggiuntiva
}

void Strategy::close_position(const OHLCV& bar, const std::string& exit_reason) {
    Trade trade;
    trade.entry_time = entry_time_;
    trade.exit_time = bar.datetime;
    trade.entry_price = entry_price_;
    trade.exit_price = bar.close;
    trade.is_long = (position_type_ == "long");
    // Calcolo PnL con commissioni
    double gross_pnl = (position_type_ == "long") ?
        (bar.close - entry_price_) * std::abs(current_position_) :
        (entry_price_ - bar.close) * std::abs(current_position_);
    double commission_cost = commission_ * (std::abs(current_position_) * (entry_price_ + bar.close));
    trade.pnl = gross_pnl - commission_cost;
    trades_.push_back(trade);
    cash_ += trade.pnl;
    current_position_ = 0.0;
    entry_price_ = 0.0;
    position_type_.clear();
    bar_in_trade_ = 0;
}

double Strategy::get_total_pnl() const {
    return std::accumulate(trades_.begin(), trades_.end(), 0.0,
        [](double sum, const Trade& trade) { return sum + trade.pnl; });
}

double Strategy::get_win_rate() const {
    if (trades_.empty()) return 0.0;
    int winning_trades = std::count_if(trades_.begin(), trades_.end(),
        [](const Trade& trade) { return trade.pnl > 0; });
    return static_cast<double>(winning_trades) / trades_.size();
}

double Strategy::get_profit_factor() const {
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

double Strategy::get_max_drawdown() const {
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