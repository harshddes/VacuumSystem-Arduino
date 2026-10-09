#!/usr/bin/env bash
set -euo pipefail
test_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT
compiler="${CXX:-g++}"
"$compiler" -std=c++11 -Wall -Wextra -Werror "$test_dir/test_bench_logic.cpp" -o "$build_dir/test_bench_logic"
"$build_dir/test_bench_logic"
"$compiler" -std=c++11 -Wall -Wextra -Werror -include "$test_dir/arduino_stub.h" -x c++ -fsyntax-only "$test_dir/../firmware/phase1_led_demo/phase1_led_demo.ino"
printf '%s\n' 'PASS: sketch host-stub syntax check. AVR target compilation and physical testing remain pending.'
