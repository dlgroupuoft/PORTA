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
// GetPlans
// @Title GetPlans
// @Tag Plan API
// @Description get plans
// @Param   owner     query    string  true        "The owner of plans"
// @Success 200 {array} object.Plan The Response object
// @router /get-plans [get]
func (c *ApiController) GetPlans() {
// GetPlan
// @Title GetPlan
// @Tag Plan API
// @Description get plan
// @Param   id     query    string  true        "The id ( owner/name ) of the plan"
// @Param   includeOption     query    bool  false        "Should include plan's option"
// @Success 200 {object} object.Plan The Response object
// @router /get-plan [get]
func (c *ApiController) GetPlan() {
// UpdatePlan
// @Title UpdatePlan
// @Tag Plan API
// @Description update plan
// @Param   id     query    string  true        "The id ( owner/name ) of the plan"
// @Param   body    body   object.Plan  true        "The details of the plan"
// @Success 200 {object} controllers.Response The Response object
// @router /update-plan [post]
func (c *ApiController) UpdatePlan() {
// AddPlan
// @Title AddPlan
// @Tag Plan API
// @Description add plan
// @Param   body    body   object.Plan  true        "The details of the plan"
// @Success 200 {object} controllers.Response The Response object
// @router /add-plan [post]
func (c *ApiController) AddPlan() {
	// Create a related product for plan
// DeletePlan
// @Title DeletePlan
// @Tag Plan API
// @Description delete plan
// @Param   body    body   object.Plan  true        "The details of the plan"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-plan [post]
func (c *ApiController) DeletePlan() {