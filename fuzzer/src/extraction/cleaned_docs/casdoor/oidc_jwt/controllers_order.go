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
package controllers
// GetOrders
// @Title GetOrders
// @Tag Order API
// @Description get orders
// @Param   owner     query    string  true        "The owner of orders"
// @Success 200 {array} object.Order The Response object
// @router /get-orders [get]
func (c *ApiController) GetOrders() {
			// If field is "user", filter by that user even for admins
// GetUserOrders
// @Title GetUserOrders
// @Tag Order API
// @Description get orders for a user
// @Param   owner     query    string  true        "The owner of orders"
// @Param   user    query   string  true           "The username of the user"
// @Success 200 {array} object.Order The Response object
// @router /get-user-orders [get]
func (c *ApiController) GetUserOrders() {
// GetOrder
// @Title GetOrder
// @Tag Order API
// @Description get order
// @Param   id     query    string  true        "The id ( owner/name ) of the order"
// @Success 200 {object} object.Order The Response object
// @router /get-order [get]
func (c *ApiController) GetOrder() {
// UpdateOrder
// @Title UpdateOrder
// @Tag Order API
// @Description update order
// @Param   id     query    string  true        "The id ( owner/name ) of the order"
// @Param   body    body   object.Order  true        "The details of the order"
// @Success 200 {object} controllers.Response The Response object
// @router /update-order [post]
func (c *ApiController) UpdateOrder() {
// AddOrder
// @Title AddOrder
// @Tag Order API
// @Description add order
// @Param   body    body   object.Order  true        "The details of the order"
// @Success 200 {object} controllers.Response The Response object
// @router /add-order [post]
func (c *ApiController) AddOrder() {
// DeleteOrder
// @Title DeleteOrder
// @Tag Order API
// @Description delete order
// @Param   body    body   object.Order  true        "The details of the order"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-order [post]
func (c *ApiController) DeleteOrder() {