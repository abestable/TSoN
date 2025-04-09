#include "dataloader.hpp"
#include <fstream>
#include <sstream>
#include <iostream>

std::vector<Candela> leggi_csv(const std::string& filepath, bool& errore_apertura) {
    std::vector<Candela> dati;
    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Errore: impossibile aprire il file '" << filepath << "'\n";
        errore_apertura = true;
        return dati;
    }

    std::string line;
    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string datetime, open, high, low, close, volume;
        std::getline(ss, datetime, ';');
        std::getline(ss, open, ';');
        std::getline(ss, high, ';');
        std::getline(ss, low, ';');
        std::getline(ss, close, ';');
        std::getline(ss, volume, ';');
        try {
            dati.push_back({datetime, std::stod(open), std::stod(high), std::stod(low)});
        } catch (...) {
            continue;
        }
    }
    return dati;
}

std::vector<double> genera_range(double min, double max, int punti) {
    std::vector<double> valori;
    if (punti <= 1) { valori.push_back(min); return valori; }
    double step = (max - min) / (punti - 1);
    for (int i = 0; i < punti; ++i)
        valori.push_back(min + i * step);
    return valori;
}
