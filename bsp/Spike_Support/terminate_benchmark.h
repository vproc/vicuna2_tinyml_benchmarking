/*
 * Copyright (C) 2024 Chair of Electronic Design Automation, TUM
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the License); you may
 * not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an AS IS BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef _TERMINATE_BENCHMARK_H
#define _TERMINATE_BENCHMARK_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

void benchmark_success();

void benchmark_failure();

void start_cycle_count();

void store_result_float(float result);

void store_result_half_float(_Float16 result);

void store_result_int(uint32_t result);

#ifdef __cplusplus
}
#endif

#endif /* _TERMINATE_BENCHMARK_H */
