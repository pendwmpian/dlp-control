#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include <iostream>

namespace py = pybind11;

py::array_t<int32_t> ERLEdecode(py::bytes input) {
    const std::string encoded(input);
    py::array_t<int32_t> ret({1080, 1920});
    int seek = 0;
    for (int i = 0; i < 1080; i++){
        if([&](){ 
            for (int j = 0; j < 1920; j++){
                if ((uint8_t) encoded[seek] == 0){
                    seek++;
                    if ((uint8_t) encoded[seek] == 0){
                        seek++;
                        if (j != 0) return false;
                    }
                    else if ((uint8_t) encoded[seek] == 1){
                        seek++;
                        int rep = (uint8_t) encoded[seek];
                        seek++;
                        if(rep == 0) return true;
                        for (int b = j; j < rep + b; j++){
                            *ret.mutable_data(i, j) = *ret.mutable_data(i - 1, j);
                        }
                        j--;
                    } else {
                        int rep = (uint8_t) encoded[seek];
                        seek++;
                        for (int b = j; j < rep + b; j++){
                            int buf = (uint8_t) encoded[seek] + ((int)(uint8_t) encoded[seek + 1] << 8) + ((int)(uint8_t) encoded[seek + 2] << 16);
                            seek += 3;
                            *ret.mutable_data(i, j) = buf;
                        }
                        j--;
                    }
                } else {
                    int rep = 0;
                    if ((uint8_t) encoded[seek] >= 128){
                        rep += (uint8_t) encoded[seek] - 128;
                        seek++;
                        rep += (uint8_t) encoded[seek] * 128;
                        seek++;
                    } else {
                        rep += (uint8_t) encoded[seek];
                        seek++;
                    }
                    int buf = (uint8_t) encoded[seek] + ((int)(uint8_t) encoded[seek + 1] << 8) + ((int)(uint8_t) encoded[seek + 2] << 16);
                    std::cout << buf << std::endl;
                    seek += 3;
                    for (int b = j; j < rep + b; j++){
                        *ret.mutable_data(i, j) = buf;
                    }
                    j--;
                }
            }
            return false;
        }()) break;
    }
    return ret;
}

PYBIND11_MODULE(enhanced_rle, m) {
    m.doc() = "module for Enhanced RLE";
    m.def("ERLEdecode", &ERLEdecode, "Decode the Enhanced RLE data to uncompressed BMP numpy array");
}