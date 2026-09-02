// Copyright 2025 The Casdoor Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
package object
type Order struct {
	// Product Info
	// User Info
	// Payment Info
	// Order State
type ProductInfo struct {
func GetOrderCount(owner, field, value string) (int64, error) {
func GetOrders(owner string) ([]*Order, error) {
func GetUserOrders(owner, user string) ([]*Order, error) {
func GetPaginationOrders(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Order, error) {
func getOrder(owner string, name string) (*Order, error) {
func GetOrder(id string) (*Order, error) {
func UpdateOrder(id string, order *Order) (bool, error) {
				// Keep historical product info; do not overwrite with current product.
func AddOrder(order *Order) (bool, error) {
func DeleteOrder(order *Order) (bool, error) {
func (order *Order) GetId() string {