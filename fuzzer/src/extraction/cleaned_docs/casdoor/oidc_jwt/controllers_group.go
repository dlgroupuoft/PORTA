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
package controllers
// GetGroups
// @Title GetGroups
// @Tag Group API
// @Description get groups
// @Param   owner     query    string  true        "The owner of groups"
// @Success 200 {array} object.Group The Response object
// @router /get-groups [get]
func (c *ApiController) GetGroups() {
// GetGroup
// @Title GetGroup
// @Tag Group API
// @Description get group
// @Param   id     query    string  true        "The id ( owner/name ) of the group"
// @Success 200 {object} object.Group The Response object
// @router /get-group [get]
func (c *ApiController) GetGroup() {
// UpdateGroup
// @Title UpdateGroup
// @Tag Group API
// @Description update group
// @Param   id     query    string  true        "The id ( owner/name ) of the group"
// @Param   body    body   object.Group  true        "The details of the group"
// @Success 200 {object} controllers.Response The Response object
// @router /update-group [post]
func (c *ApiController) UpdateGroup() {
// AddGroup
// @Title AddGroup
// @Tag Group API
// @Description add group
// @Param   body    body   object.Group  true      "The details of the group"
// @Success 200 {object} controllers.Response The Response object
// @router /add-group [post]
func (c *ApiController) AddGroup() {
// DeleteGroup
// @Title DeleteGroup
// @Tag Group API
// @Description delete group
// @Param   body    body   object.Group  true        "The details of the group"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-group [post]
func (c *ApiController) DeleteGroup() {