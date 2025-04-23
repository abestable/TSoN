#pragma once

#include <vector>
#include <string>

// Funzione per stampare uno shmoo plot in ASCII
void stampa_shmoo_plot(const std::vector<double>& tp_list, 
                      const std::vector<double>& sl_list,
                      const std::vector<std::vector<double>>& roi_matrix,
                      const std::string& title = "ROI Shmoo Plot"); 