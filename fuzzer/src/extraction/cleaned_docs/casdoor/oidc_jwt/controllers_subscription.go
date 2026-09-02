// Copyright 2023 The Casdoor Authors. All Rights Reserved.
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
// GetSubscriptions
// @Title GetSubscriptions
// @Tag Subscription API
// @Description get subscriptions
// @Param   owner     query    string  true        "The owner of subscriptions"
// @Success 200 {array} object.Subscription The Response object
// @router /get-subscriptions [get]
func (c *ApiController) GetSubscriptions() {
			// If field is "user", filter by that user even for admins
// GetSubscription
// @Title GetSubscription
// @Tag Subscription API
// @Description get subscription
// @Param   id     query    string  true        "The id ( owner/name ) of the subscription"
// @Success 200 {object} object.Subscription The Response object
// @router /get-subscription [get]
func (c *ApiController) GetSubscription() {
// UpdateSubscription
// @Title UpdateSubscription
// @Tag Subscription API
// @Description update subscription
// @Param   id     query    string  true        "The id ( owner/name ) of the subscription"
// @Param   body    body   object.Subscription  true        "The details of the subscription"
// @Success 200 {object} controllers.Response The Response object
// @router /update-subscription [post]
func (c *ApiController) UpdateSubscription() {
// AddSubscription
// @Title AddSubscription
// @Tag Subscription API
// @Description add subscription
// @Param   body    body   object.Subscription  true        "The details of the subscription"
// @Success 200 {object} controllers.Response The Response object
// @router /add-subscription [post]
func (c *ApiController) AddSubscription() {
	// Check if plan restricts user to one subscription
// DeleteSubscription
// @Title DeleteSubscription
// @Tag Subscription API
// @Description delete subscription
// @Param   body    body   object.Subscription  true        "The details of the subscription"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-subscription [post]
func (c *ApiController) DeleteSubscription() {