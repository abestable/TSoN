#pragma once
#include <string>

void stampa_intestazione_tabella();
void stampa_riga(double tp, double sl, const std::string& direzione, double percent_success, double ricavi, double capitale, double perdite, double fee_totali, double roi, int non_chiusi);
void stampa_fine_tabella();
