#include "printer.hpp"
#include <iostream>
#include <iomanip>

void stampa_intestazione_tabella() {
    std::cout << "+-------------+-------------+------------+---------------+----------------+----------------+----------------+----------------+-------------+------------+\n";
    std::cout << "| TP %        | SL %        | Direzione  | % Successi    | Ricavi €       | Saldo €        | Perdite €      | Fee €          | ROI netto   | Non chiusi |\n";
    std::cout << "+-------------+-------------+------------+---------------+----------------+----------------+----------------+----------------+-------------+------------+\n";
}

void stampa_riga(double tp, double sl, const std::string& direzione, double percent_success, double ricavi, double capitale, double perdite, double fee_totali, double roi, int non_chiusi) {
    std::cout << "| " << std::setw(10) << std::fixed << std::setprecision(5) << tp  << "% "
              << "| " << std::setw(10) << sl << "% "
              << "| " << std::setw(10) << direzione << " "
              << "| " << std::setw(12) << std::setprecision(2) << percent_success << "% "
              << "| " << std::setw(12) << ricavi << " € "
              << "| " << std::setw(12) << capitale << " € "
              << "| " << std::setw(12) << perdite << " € "
              << "| " << std::setw(12) << fee_totali << " € "
              << "| " << std::setw(10) << roi << "% "
              << "| " << std::setw(10) << non_chiusi << " |\n";
}

void stampa_fine_tabella() {
    std::cout << "+-------------+-------------+------------+---------------+----------------+----------------+----------------+----------------+-------------+------------+\n";
}
