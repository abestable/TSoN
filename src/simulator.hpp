#pragma once
#include "dataloader.hpp"
#include <vector>

void simula(const std::vector<double>& tp_list, const std::vector<double>& sl_list,
            const std::vector<Candela>& dati, size_t finestra,
            double capitale_per_trade, double fee, int periodo, bool EXIT_MODE_CLOSE, double capitale_iniziale);
