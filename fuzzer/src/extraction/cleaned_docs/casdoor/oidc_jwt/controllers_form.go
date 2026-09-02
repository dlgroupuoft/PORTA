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
// GetGlobalForms
// @Title GetGlobalForms
// @Tag Form API
// @Description get global forms
// @Success 200 {array} object.Form The Response object
// @router /get-global-forms [get]
func (c *ApiController) GetGlobalForms() {
// GetForms
// @Title GetForms
// @Tag Form API
// @Description get forms
// @Param owner query string true "The owner of form"
// @Success 200 {array} object.Form The Response object
// @router /get-forms [get]
func (c *ApiController) GetForms() {
// GetForm
// @Title GetForm
// @Tag Form API
// @Description get form
// @Param id query string true "The id (owner/name) of form"
// @Success 200 {object} object.Form The Response object
// @router /get-form [get]
func (c *ApiController) GetForm() {
// UpdateForm
// @Title UpdateForm
// @Tag Form API
// @Description update form
// @Param id query string true "The id (owner/name) of the form"
// @Param body body object.Form true "The details of the form"
// @Success 200 {object} controllers.Response The Response object
// @router /update-form [post]
func (c *ApiController) UpdateForm() {
// AddForm
// @Title AddForm
// @Tag Form API
// @Description add form
// @Param body body object.Form true "The details of the form"
// @Success 200 {object} controllers.Response The Response object
// @router /add-form [post]
func (c *ApiController) AddForm() {
// DeleteForm
// @Title DeleteForm
// @Tag Form API
// @Description delete form
// @Param body body object.Form true "The details of the form"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-form [post]
func (c *ApiController) DeleteForm() {