CXX = g++
CXXFLAGS = -Wall -O3 -std=c++17
LDFLAGS = 
SRC = src/main.cpp src/dataloader.cpp src/printer.cpp src/simulator.cpp
OBJ = $(SRC:.cpp=.o)
TARGET = simulatore_trading

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

clean:
	rm -f $(OBJ) $(TARGET)
