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
// GetRoles
// @Title GetRoles
// @Tag Role API
// @Description get roles
// @Param   owner     query    string  true        "The owner of roles"
// @Success 200 {array} object.Role The Response object
// @router /get-roles [get]
func (c *ApiController) GetRoles() {
// GetRole
// @Title GetRole
// @Tag Role API
// @Description get role
// @Param   id     query    string  true        "The id ( owner/name ) of the role"
// @Success 200 {object} object.Role The Response object
// @router /get-role [get]
func (c *ApiController) GetRole() {
// UpdateRole
// @Title UpdateRole
// @Tag Role API
// @Description update role
// @Param   id     query    string  true        "The id ( owner/name ) of the role"
// @Param   body    body   object.Role  true        "The details of the role"
// @Success 200 {object} controllers.Response The Response object
// @router /update-role [post]
func (c *ApiController) UpdateRole() {
// AddRole
// @Title AddRole
// @Tag Role API
// @Description add role
// @Param   body    body   object.Role  true        "The details of the role"
// @Success 200 {object} controllers.Response The Response object
// @router /add-role [post]
func (c *ApiController) AddRole() {
// DeleteRole
// @Title DeleteRole
// @Tag Role API
// @Description delete role
// @Param   body    body   object.Role  true        "The details of the role"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-role [post]
func (c *ApiController) DeleteRole() {