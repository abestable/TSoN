#pragma once
#include <vector>
#include <string>

struct Candela {
    std::string datetime;
    double open;
    double high;
    double low;
    double close;
};

std::vector<Candela> leggi_csv(const std::string& filepath, bool& errore_apertura);
std::vector<double> genera_range(double min, double max, int punti);
