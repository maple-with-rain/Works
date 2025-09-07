#ifndef MARTIX_H
#define MARTIX_H
#endif
#include <iostream>
#include <vector>
#include <stdexcept>
#include <iomanip>
#include <initializer_list>
class Martix
{
private:
    std::vector<std::vector<double>> data;
    size_t rows;
    size_t cols;
public:
    Martix() : rows(0), cols(0) {}
    
};