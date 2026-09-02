// Copyright 2021 The Casdoor Authors. All Rights Reserved.
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
// GetWebhooks
// @Title GetWebhooks
// @Tag Webhook API
// @Description get webhooks
// @Param   owner     query    string  built-in/admin	true        "The owner of webhooks"
// @Success 200 {array} object.Webhook The Response object
// @router /get-webhooks [get]
// @Security test_apiKey
func (c *ApiController) GetWebhooks() {
// GetWebhook
// @Title GetWebhook
// @Tag Webhook API
// @Description get webhook
// @Param   id     query    string  built-in/admin	true        "The id ( owner/name ) of the webhook"
// @Success 200 {object} object.Webhook The Response object
// @router /get-webhook [get]
func (c *ApiController) GetWebhook() {
// UpdateWebhook
// @Title UpdateWebhook
// @Tag Webhook API
// @Description update webhook
// @Param   id     query    string  built-in/admin true        "The id ( owner/name ) of the webhook"
// @Param   body    body   object.Webhook  true        "The details of the webhook"
// @Success 200 {object} controllers.Response The Response object
// @router /update-webhook [post]
func (c *ApiController) UpdateWebhook() {
// AddWebhook
// @Title AddWebhook
// @Tag Webhook API
// @Description add webhook
// @Param   body    body   object.Webhook  true        "The details of the webhook"
// @Success 200 {object} controllers.Response The Response object
// @router /add-webhook [post]
func (c *ApiController) AddWebhook() {
// DeleteWebhook
// @Title DeleteWebhook
// @Tag Webhook API
// @Description delete webhook
// @Param   body    body   object.Webhook  true        "The details of the webhook"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-webhook [post]
func (c *ApiController) DeleteWebhook() {