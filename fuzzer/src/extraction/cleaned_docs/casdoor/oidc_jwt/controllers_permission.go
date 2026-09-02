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
// GetPermissions
// @Title GetPermissions
// @Tag Permission API
// @Description get permissions
// @Param   owner     query    string  true        "The owner of permissions"
// @Success 200 {array} object.Permission The Response object
// @router /get-permissions [get]
func (c *ApiController) GetPermissions() {
// GetPermissionsBySubmitter
// @Title GetPermissionsBySubmitter
// @Tag Permission API
// @Description get permissions by submitter
// @Success 200 {array} object.Permission The Response object
// @router /get-permissions-by-submitter [get]
func (c *ApiController) GetPermissionsBySubmitter() {
// GetPermissionsByRole
// @Title GetPermissionsByRole
// @Tag Permission API
// @Description get permissions by role
// @Param   id     query    string  true        "The id ( owner/name ) of the role"
// @Success 200 {array} object.Permission The Response object
// @router /get-permissions-by-role [get]
func (c *ApiController) GetPermissionsByRole() {
// GetPermission
// @Title GetPermission
// @Tag Permission API
// @Description get permission
// @Param   id     query    string  true        "The id ( owner/name ) of the permission"
// @Success 200 {object} object.Permission The Response object
// @router /get-permission [get]
func (c *ApiController) GetPermission() {
// UpdatePermission
// @Title UpdatePermission
// @Tag Permission API
// @Description update permission
// @Param   id     query    string  true        "The id ( owner/name ) of the permission"
// @Param   body    body   object.Permission  true        "The details of the permission"
// @Success 200 {object} controllers.Response The Response object
// @router /update-permission [post]
func (c *ApiController) UpdatePermission() {
// AddPermission
// @Title AddPermission
// @Tag Permission API
// @Description add permission
// @Param   body    body   object.Permission  true        "The details of the permission"
// @Success 200 {object} controllers.Response The Response object
// @router /add-permission [post]
func (c *ApiController) AddPermission() {
// DeletePermission
// @Title DeletePermission
// @Tag Permission API
// @Description delete permission
// @Param   body    body   object.Permission  true        "The details of the permission"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-permission [post]
func (c *ApiController) DeletePermission() {