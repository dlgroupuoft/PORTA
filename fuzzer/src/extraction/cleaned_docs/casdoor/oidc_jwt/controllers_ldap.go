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
type LdapResp struct {
	// Groups []LdapRespGroup `json:"groups"`
// type LdapRespGroup struct {
//	GroupId   string
//	GroupName string
// }
type LdapSyncResp struct {
// GetLdapUsers
// @Title GetLdapser
// @Tag Account API
// @Description get ldap users
// Param	id	string	true	"id"
// @Success 200 {object} controllers.LdapResp The Response object
// @router /get-ldap-users [get]
func (c *ApiController) GetLdapUsers() {
	// groupsMap, err := conn.GetLdapGroups(ldapServer.BaseDn)
	// if err != nil {
	//  c.ResponseError(err.Error())
	//	return
	// }
	// for _, group := range groupsMap {
	//	resp.Groups = append(resp.Groups, LdapRespGroup{
	//		GroupId:   group.GidNumber,
	//		GroupName: group.Cn,
	//	})
	// }
// GetLdaps
// @Title GetLdaps
// @Tag Account API
// @Description get ldaps
// @Param	owner	query	string	false	"owner"
// @Success 200 {array} object.Ldap The Response object
// @router /get-ldaps [get]
func (c *ApiController) GetLdaps() {
// GetLdap
// @Title GetLdap
// @Tag Account API
// @Description get ldap
// @Param	id	query	string	true	"id"
// @Success 200 {object} object.Ldap The Response object
// @router /get-ldap [get]
func (c *ApiController) GetLdap() {
// AddLdap
// @Title AddLdap
// @Tag Account API
// @Description add ldap
// @Param	body	body	object.Ldap		true	"The details of the ldap"
// @Success 200 {object} controllers.Response The Response object
// @router /add-ldap [post]
func (c *ApiController) AddLdap() {
// UpdateLdap
// @Title UpdateLdap
// @Tag Account API
// @Description update ldap
// @Param	body	body	object.Ldap		true	"The details of the ldap"
// @Success 200 {object} controllers.Response The Response object
// @router /update-ldap [post]
func (c *ApiController) UpdateLdap() {
// DeleteLdap
// @Title DeleteLdap
// @Tag Account API
// @Description delete ldap
// @Param	body	body	object.Ldap		true	"The details of the ldap"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-ldap [post]
func (c *ApiController) DeleteLdap() {
// SyncLdapUsers
// @Title SyncLdapUsers
// @Tag Account API
// @Description sync ldap users
// @Param	id	query	string		true	"id"
// @Success 200 {object} controllers.LdapSyncResp The Response object
// @router /sync-ldap-users [post]
func (c *ApiController) SyncLdapUsers() {