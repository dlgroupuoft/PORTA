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
// GetEnforcers
// @Title GetEnforcers
// @Tag Enforcer API
// @Description get enforcers
// @Param   owner     query    string  true        "The owner of enforcers"
// @Success 200 {array} object.Enforcer
// @router /get-enforcers [get]
func (c *ApiController) GetEnforcers() {
// GetEnforcer
// @Title GetEnforcer
// @Tag Enforcer API
// @Description get enforcer
// @Param   id     query    string  true        "The id ( owner/name )  of enforcer"
// @Success 200 {object} object.Enforcer
// @router /get-enforcer [get]
func (c *ApiController) GetEnforcer() {
// UpdateEnforcer
// @Title UpdateEnforcer
// @Tag Enforcer API
// @Description update enforcer
// @Param   id     query    string  true        "The id ( owner/name )  of enforcer"
// @Param   enforcer     body    object  true        "The enforcer object"
// @Success 200 {object} object.Enforcer
// @router /update-enforcer [post]
func (c *ApiController) UpdateEnforcer() {
// AddEnforcer
// @Title AddEnforcer
// @Tag Enforcer API
// @Description add enforcer
// @Param   enforcer     body    object  true        "The enforcer object"
// @Success 200 {object} object.Enforcer
// @router /add-enforcer [post]
func (c *ApiController) AddEnforcer() {
// DeleteEnforcer
// @Title DeleteEnforcer
// @Tag Enforcer API
// @Description delete enforcer
// @Param   body    body    object.Enforcer  true      "The enforcer object"
// @Success 200 {object} object.Enforcer
// @router /delete-enforcer [post]
func (c *ApiController) DeleteEnforcer() {
// GetPolicies
// @Title GetPolicies
// @Tag Enforcer API
// @Description get policies
// @Param   id     query    string  true        "The id ( owner/name )  of enforcer"
// @Param   adapterId     query    string  false        "The adapter id"
// @Success 200 {array} xormadapter.CasbinRule
// @router /get-policies [get]
func (c *ApiController) GetPolicies() {
// GetFilteredPolicies
// @Title GetFilteredPolicies
// @Tag Enforcer API
// @Description get filtered policies with support for multiple filters via POST body
// @Param   id     query    string  true        "The id ( owner/name )  of enforcer"
// @Param   body   body    []object.Filter  true        "Array of filter objects for multiple filters"
// @Success 200 {array} xormadapter.CasbinRule
// @router /get-filtered-policies [post]
func (c *ApiController) GetFilteredPolicies() {
// UpdatePolicy
// @Title UpdatePolicy
// @Tag Enforcer API
// @Description update policy
// @Param   id     query    string  true        "The id ( owner/name )  of enforcer"
// @Param   body     body    []xormadapter.CasbinRule  true        "Array containing old and new policy"
// @Success 200 {object} Response
// @router /update-policy [post]
func (c *ApiController) UpdatePolicy() {
// AddPolicy
// @Title AddPolicy
// @Tag Enforcer API
// @Description add policy
// @Param   id     query    string  true        "The id ( owner/name )  of enforcer"
// @Param   body     body    xormadapter.CasbinRule  true        "The policy to add"
// @Success 200 {object} Response
// @router /add-policy [post]
func (c *ApiController) AddPolicy() {
// RemovePolicy
// @Title RemovePolicy
// @Tag Enforcer API
// @Description remove policy
// @Param   id     query    string  true        "The id ( owner/name )  of enforcer"
// @Param   body     body    xormadapter.CasbinRule  true        "The policy to remove"
// @Success 200 {object} Response
// @router /remove-policy [post]
func (c *ApiController) RemovePolicy() {