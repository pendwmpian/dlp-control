#include <string>
#include <vector>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

py::bytes ERLEencode(py::array_t<int32_t> input) {
    std::vector<char> buf;
    for (int i = 0; i < 1080; i++){
        std::vector<int> r(1920, -1), c(1920, -1), u(1920, -1), dp(1920, 1 << 30);
        std::vector<char> mode(1920); // r for repeat, c for copy, u for uncompressed mode
        for (int j = 0; j < 1920; j++){
            // Repeat
            if (j == 0){
                r[0] = 0;
            } else {
                if (*input.data(i, j) == *input.data(i, j - 1)) r[j] = r[j - 1];
                else r[j] = j;
            }
            // Copy
            if (i != 0){
                if (*input.data(i, j) != *input.data(i - 1, j)) c[j] = -1;
                else if (j != 0 && c[j - 1] != -1) c[j] = c[j - 1];
                else c[j] = j; 
            }
            // dp
            if (j == 0) {
                dp[0] = 4;
                mode[0] = 'r';
            }
            else {
                std::vector<int> cost, u_;
                std::vector<char> choice;
                // repeat
                cost.push_back(dp[r[j] - 1] + ((j - r[j] > 127)? 5 : 4));
                u_.push_back(0);
                choice.push_back('r');
                // copy
                if (c[j] != -1) {
                    cost.push_back(dp[c[j] - 1] + ((j - c[j] > 127)? 4 : 3));
                    u_.push_back(0);
                    choice.push_back('c');
                }
                // uncompressed
                for (int l = 1; l < 4; l++){
                    if(j - l < 0) break;
                    if(u[j - l] > 0){
                        cost.push_back(dp[j - l] + 3 * l + ((u[j - l] >= 128 - l)? 1 : 0));
                        u_.push_back(u[j - l] + l);
                        choice.push_back('u');
                    } else {
                        if (l == 1) continue;
                        cost.push_back(dp[j - l] + 3 * l + 2);
                        u_.push_back(l);
                        choice.push_back('u');
                    }
                }
                // dp update
                auto min_itr = std::min_element(cost.begin(), cost.end());
                dp[j] = *min_itr;
                u[j] = u_[min_itr - cost.begin()];
                mode[j] = choice[min_itr - cost.begin()];
            }
        }
        // dp reconstruction
        std::vector<std::pair<char, int>> key;
        int seek = 1919;
        while (seek >= 0){
            int len;
            switch (mode[seek]) {
                case 'r':
                    len = seek - r[seek] + 1;
                    key.push_back(std::make_pair('r', len));
                    break;
                case 'c':
                    len = seek - c[seek] + 1;
                    key.push_back(std::make_pair('c', len));
                    break;
                case 'u':
                    len = u[seek];
                    key.push_back(std::make_pair('u', len));
                    break;
            }
            seek -= len;
        }
        seek = 0;
        std::for_each(key.rbegin(), key.rend(), [&](const auto& k){
            auto write_color = [&buf](int num){
                buf.push_back(num & 0xFF);
                buf.push_back((num >> 8) & 0xFF);
                buf.push_back((num >> 16) & 0xFF);
            };
            auto write_len = [&buf](int len){
                if(len < 128) buf.push_back(len);
                else {
                    buf.push_back((len & 0x7F) | 0x80);
                    buf.push_back((len >> 7) & 0xFF);
                }
            };
            switch (k.first) {
                case 'r':
                    write_len(k.second);
                    write_color(*input.data(i, seek));
                    break;
                case 'c':
                    buf.push_back(0);
                    buf.push_back(1);
                    write_len(k.second);
                    break;
                case 'u':
                    buf.push_back(0);
                    write_len(k.second);
                    for (int l = 0; l < k.second; l++) write_color(*input.data(i, seek + l));
                    break;
            }
            seek += k.second;
        });
        // End-of-line (optional)
        buf.push_back(0);
        buf.push_back(0);
    }
    // End-of-image (optional)
    buf.push_back(0);
    buf.push_back(1);
    buf.push_back(0);

    return py::bytes(buf.data(), buf.size());
}

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
    m.def("ERLEencode", &ERLEencode, "Compress the uncompressed BMP numpy array to Enhanced RLE data");
    m.def("ERLEdecode", &ERLEdecode, "Decode the Enhanced RLE data to uncompressed BMP numpy array");
}