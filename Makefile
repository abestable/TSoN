# Makefile per simulatore_trading

CXX = g++
CXXFLAGS = -Wall -O3 -std=c++17
SRC = simulatore_trading.cpp
OUT = simulatore_trading

all: $(OUT)

$(OUT): $(SRC)
	$(CXX) $(CXXFLAGS) -o $@ $^

clean:
	rm -f $(OUT)
