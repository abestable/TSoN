#include "plotter.hpp"
#include <iostream>
#include <iomanip>
#include <algorithm>
#include <cmath>
#include <limits>
#include <vector>

// Colori ANSI
const char* COLORS[] = {
    "\033[31m",  // Rosso
    "\033[91m",  // Rosso chiaro
    "\033[93m",  // Giallo
    "\033[92m",  // Verde chiaro
    "\033[32m",  // Verde
};
const char* RESET = "\033[0m";

void stampa_shmoo_plot(const std::vector<double>& tp_list, 
                      const std::vector<double>& sl_list,
                      const std::vector<std::vector<double>>& roi_matrix,
                      const std::string& title) {
    // Trova i valori min e max per la scala dei colori
    double min_roi = std::numeric_limits<double>::max();
    double max_roi = std::numeric_limits<double>::lowest();
    
    for (const auto& row : roi_matrix) {
        for (double roi : row) {
            min_roi = std::min(min_roi, roi);
            max_roi = std::max(max_roi, roi);
        }
    }
    
    // Stampa il titolo
    std::cout << "\n" << title << "\n\n";
    
    // Stampa l'intestazione con i valori di TP
    std::cout << "SL\\TP ";
    for (double tp : tp_list) {
        std::cout << std::setw(8) << std::fixed << std::setprecision(2) << tp << "% ";
    }
    std::cout << "\n";
    
    // Stampa una linea separatrice
    std::cout << std::string(6 + tp_list.size() * 10, '-') << "\n";
    
    // Stampa la matrice con i colori
    for (size_t i = 0; i < sl_list.size(); ++i) {
        std::cout << std::setw(5) << std::fixed << std::setprecision(2) << sl_list[i] << "% ";
        
        for (size_t j = 0; j < tp_list.size(); ++j) {
            double roi = roi_matrix[i][j];
            
            // Calcola l'indice del colore da usare
            int color_index;
            if (roi == min_roi) {
                color_index = 0;  // Rosso per il valore minimo
            } else if (roi == max_roi) {
                color_index = sizeof(COLORS)/sizeof(COLORS[0]) - 1;  // Verde per il valore massimo
            } else {
                // Mappa il ROI su un indice di colore
                double range = max_roi - min_roi;
                if (range == 0) {
                    color_index = 0;
                } else {
                    double normalized = (roi - min_roi) / range;
                    color_index = static_cast<int>(normalized * (sizeof(COLORS)/sizeof(COLORS[0]) - 1));
                    color_index = std::max(0, std::min(color_index, static_cast<int>(sizeof(COLORS)/sizeof(COLORS[0]) - 1)));
                }
            }
            
            // Stampa il valore con il colore appropriato
            std::cout << COLORS[color_index] << std::setw(8) << std::fixed << std::setprecision(2) << roi << "% " << RESET;
        }
        
        std::cout << "\n";
    }
    
    // Stampa una legenda
    std::cout << "\nLegenda:\n";
    int num_colors = sizeof(COLORS)/sizeof(COLORS[0]);
    double step = (max_roi - min_roi) / (num_colors - 1);
    
    for (int i = 0; i < num_colors; ++i) {
        double roi_value = min_roi + i * step;
        std::cout << COLORS[i] << "■ " << std::fixed << std::setprecision(2) << roi_value << "% " << RESET;
    }
    std::cout << "\n\n";
} 