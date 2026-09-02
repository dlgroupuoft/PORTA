// Copyright 2022 The Casdoor Authors. All Rights Reserved.
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
type Product struct {
func GetProductCount(owner, field, value string) (int64, error) {
func GetProducts(owner string) ([]*Product, error) {
func GetPaginationProducts(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Product, error) {
func getProduct(owner string, name string) (*Product, error) {
func GetProduct(id string) (*Product, error) {
func UpdateProductStock(productInfos []ProductInfo) error {
func UpdateProduct(id string, product *Product) (bool, error) {
func AddProduct(product *Product) (bool, error) {
func checkProduct(product *Product) error {
func DeleteProduct(product *Product) (bool, error) {
func (product *Product) GetId() string {
func (product *Product) isValidProvider(provider *Provider) error {
func (product *Product) getProvider(providerName string) (*Provider, error) {
func ExtendProductWithProviders(product *Product) error {
func CreateProductForPlan(plan *Plan) *Product {
func UpdateProductForPlan(plan *Plan, product *Product) {
func getOrderProducts(owner string, productNames []string) ([]Product, error) {
func validateProductCurrencies(products []Product, orderCurrency string) error {