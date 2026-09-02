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
// PlaceOrder
// @Title PlaceOrder
// @Tag Order API
// @Description place an order for a product
// @Param   productId     query    string  true        "The id ( owner/name ) of the product"
// @Param   pricingName   query    string  false       "The name of the pricing (for subscription)"
// @Param   planName      query    string  false       "The name of the plan (for subscription)"
// @Param   customPrice   query    number  false       "Custom price for recharge products"
// @Param   userName      query    string  false       "The username to place order for (admin only)"
// @Success 200 {object} object.Order The Response object
// @router /place-order [post]
func (c *ApiController) PlaceOrder() {
// PayOrder
// @Title PayOrder
// @Tag Order API
// @Description pay an existing order
// @Param   id     query    string  true        "The id ( owner/name ) of the order"
// @Param   providerName    query    string  true  "The name of the provider"
// @Success 200 {object} controllers.Response The Response object
// @router /pay-order [post]
func (c *ApiController) PayOrder() {
// CancelOrder
// @Title CancelOrder
// @Tag Order API
// @Description cancel an order
// @Param   id     query    string  true        "The id ( owner/name ) of the order"
// @Success 200 {object} controllers.Response The Response object
// @router /cancel-order [post]
func (c *ApiController) CancelOrder() {