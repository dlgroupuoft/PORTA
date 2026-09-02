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
package controllers
// GetProducts
// @Title GetProducts
// @Tag Product API
// @Description get products
// @Param   owner     query    string  true        "The owner of products"
// @Success 200 {array} object.Product The Response object
// @router /get-products [get]
func (c *ApiController) GetProducts() {
// GetProduct
// @Title GetProduct
// @Tag Product API
// @Description get product
// @Param   id     query    string  true        "The id ( owner/name ) of the product"
// @Success 200 {object} object.Product The Response object
// @router /get-product [get]
func (c *ApiController) GetProduct() {
// UpdateProduct
// @Title UpdateProduct
// @Tag Product API
// @Description update product
// @Param   id     query    string  true        "The id ( owner/name ) of the product"
// @Param   body    body   object.Product  true        "The details of the product"
// @Success 200 {object} controllers.Response The Response object
// @router /update-product [post]
func (c *ApiController) UpdateProduct() {
// AddProduct
// @Title AddProduct
// @Tag Product API
// @Description add product
// @Param   body    body   object.Product  true        "The details of the product"
// @Success 200 {object} controllers.Response The Response object
// @router /add-product [post]
func (c *ApiController) AddProduct() {
// DeleteProduct
// @Title DeleteProduct
// @Tag Product API
// @Description delete product
// @Param   body    body   object.Product  true        "The details of the product"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-product [post]
func (c *ApiController) DeleteProduct() {