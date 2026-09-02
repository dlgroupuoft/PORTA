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
// Enforce
// @Title Enforce
// @Tag Enforcer API
// @Description Call Casbin Enforce API
// @Param   body    body   []string  true   "Casbin request"
// @Param   permissionId    query   string  false   "permission id"
// @Param   modelId    query   string  false   "model id"
// @Param   resourceId    query   string  false   "resource id"
// @Param   owner    query   string  false   "owner"
// @Success 200 {object} controllers.Response The Response object
// @router /enforce [post]
func (c *ApiController) Enforce() {
		// type transformation
// BatchEnforce
// @Title BatchEnforce
// @Tag Enforcer API
// @Description Call Casbin BatchEnforce API
// @Param   body    body   []string  true   "array of casbin requests"
// @Param   permissionId    query   string  false   "permission id"
// @Param   modelId    query   string  false   "model id"
// @Param   owner    query   string  false   "owner"
// @Success 200 {object} controllers.Response The Response object
// @router /batch-enforce [post]
func (c *ApiController) BatchEnforce() {
		// type transformation
// GetAllObjects
// @Title GetAllObjects
// @Tag Enforcer API
// @Description Get all objects for a user (Casbin API)
// @Param   userId    query   string  false   "user id like built-in/admin"
// @Success 200 {object} controllers.Response The Response object
// @router /get-all-objects [get]
func (c *ApiController) GetAllObjects() {
// GetAllActions
// @Title GetAllActions
// @Tag Enforcer API
// @Description Get all actions for a user (Casbin API)
// @Param   userId    query   string  false   "user id like built-in/admin"
// @Success 200 {object} controllers.Response The Response object
// @router /get-all-actions [get]
func (c *ApiController) GetAllActions() {
// GetAllRoles
// @Title GetAllRoles
// @Tag Enforcer API
// @Description Get all roles for a user (Casbin API)
// @Param   userId    query   string  false   "user id like built-in/admin"
// @Success 200 {object} controllers.Response The Response object
// @router /get-all-roles [get]
func (c *ApiController) GetAllRoles() {