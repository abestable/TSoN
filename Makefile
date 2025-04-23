CXX = g++
CXXFLAGS = -O3 -Wall -std=c++17
PYTHON_INCLUDE = $(shell python3 -m pybind11 --includes)
PYTHON_LIBS = $(shell python3-config --ldflags)

SRCS = src/main.cpp src/dataloader.cpp src/printer.cpp src/simulator.cpp src/plotter.cpp
OBJS = $(SRCS:.cpp=.o)
TARGET = simulatore_trading

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(OBJS) -o $(TARGET) $(PYTHON_LIBS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) $(PYTHON_INCLUDE) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all clean
