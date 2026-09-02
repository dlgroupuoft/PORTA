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
// GetGlobalUsers
// @Title GetGlobalUsers
// @Tag User API
// @Description get global users
// @Success 200 {array} object.User The Response object
// @router /get-global-users [get]
func (c *ApiController) GetGlobalUsers() {
// GetUsers
// @Title GetUsers
// @Tag User API
// @Description
// @Param   owner     query    string  true        "The owner of users"
// @Success 200 {array} object.User The Response object
// @router /get-users [get]
func (c *ApiController) GetUsers() {
// GetUser
// @Title GetUser
// @Tag User API
// @Description get user
// @Param   id     query    string  false        "The id ( owner/name ) of the user"
// @Param   owner  query    string  false        "The owner of the user"
// @Param   email  query    string  false 	     "The email of the user"
// @Param   phone  query    string  false 	     "The phone of the user"
// @Param   userId query    string  false 	     "The userId of the user"
// @Success 200 {object} object.User The Response object
// @router /get-user [get]
func (c *ApiController) GetUser() {
// UpdateUser
// @Title UpdateUser
// @Tag User API
// @Description update user
// @Param   id     query    string  false        "The id ( owner/name ) of the user"
// @Param   userId query    string  false        "The userId (UUID) of the user"
// @Param   owner  query    string  false        "The owner of the user (required when using userId)"
// @Param   body    body   object.User  true        "The details of the user"
// @Success 200 {object} controllers.Response The Response object
// @router /update-user [post]
func (c *ApiController) UpdateUser() {
// AddUser
// @Title AddUser
// @Tag User API
// @Description add user
// @Param   body    body   object.User  true        "The details of the user"
// @Success 200 {object} controllers.Response The Response object
// @router /add-user [post]
func (c *ApiController) AddUser() {
	// Set RegisterSource based on the current user if not already set
// DeleteUser
// @Title DeleteUser
// @Tag User API
// @Description delete user
// @Param   body    body   object.User  true        "The details of the user"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-user [post]
func (c *ApiController) DeleteUser() {
// GetEmailAndPhone
// @Title GetEmailAndPhone
// @Tag User API
// @Description get email and phone by username
// @Param   username    formData   string  true        "The username of the user"
// @Param   organization    formData   string  true        "The organization of the user"
// @Success 200 {object} controllers.Response The Response object
// @router /get-email-and-phone [get]
func (c *ApiController) GetEmailAndPhone() {
// SetPassword
// @Title SetPassword
// @Tag Account API
// @Description set password
// @Param   userOwner   formData    string  true        "The owner of the user"
// @Param   userName   formData    string  true        "The name of the user"
// @Param   oldPassword   formData    string  true        "The old password of the user"
// @Param   newPassword   formData    string  true        "The new password of the user"
// @Success 200 {object} controllers.Response The Response object
// @router /set-password [post]
func (c *ApiController) SetPassword() {
	// if userOwner == "built-in" && userName == "admin" {
	//	c.ResponseError(c.T("auth:Unauthorized operation"))
	//	return
	// }
	// Get organization to check for password obfuscation settings
	// Deobfuscate passwords if organization has password obfuscator configured
	// Note: Deobfuscation is optional - if it fails, we treat the password as plain text
	// This allows SDKs and raw HTTP API calls to work without obfuscation support
	// Check if the new password is the same as the current password
// CheckUserPassword
// @Title CheckUserPassword
// @router /check-user-password [post]
// @Tag User API
// @Success 200 {object} object.Userinfo The Response object
func (c *ApiController) CheckUserPassword() {
// GetSortedUsers
// @Title GetSortedUsers
// @Tag User API
// @Description
// @Param   owner     query    string  true        "The owner of users"
// @Param   sorter     query    string  true        "The DB column name to sort by, e.g., created_time"
// @Param   limit     query    string  true        "The count of users to return, e.g., 25"
// @Success 200 {array} object.User The Response object
// @router /get-sorted-users [get]
func (c *ApiController) GetSortedUsers() {
// GetUserCount
// @Title GetUserCount
// @Tag User API
// @Description
// @Param   owner     query    string  true        "The owner of users"
// @Param   isOnline     query    string  true        "The filter for query, 1 for online, 0 for offline, empty string for all users"
// @Success 200 {int} int The count of filtered users for an organization
// @router /get-user-count [get]
func (c *ApiController) GetUserCount() {
// AddUserKeys
// @Title AddUserKeys
// @router /add-user-keys [post]
// @Tag User API
// @Success 200 {object} object.Userinfo The Response object
func (c *ApiController) AddUserKeys() {
func (c *ApiController) RemoveUserFromGroup() {
// ImpersonateUser
// @Title ImpersonateUser
// @Tag User API
// @Description set impersonation user for current admin session
// @Param   username    formData   string  true        "The username to impersonate (owner/name)"
// @Success 200 {object} controllers.Response The Response object
// @router /impersonation-user [post]
func (c *ApiController) ImpersonateUser() {
// ExitImpersonateUser
// @Title ExitImpersonateUser
// @Tag User API
// @Description clear impersonation info for current session
// @Success 200 {object} controllers.Response The Response object
// @router /exit-impersonation-user [post]
func (c *ApiController) ExitImpersonateUser() {
// VerifyIdentification
// @Title VerifyIdentification
// @Tag User API
// @Description verify user's real identity using ID Verification provider
// @Param   owner     query    string  false  "The owner of the user (optional, defaults to logged-in user)"
// @Param   name      query    string  false  "The name of the user (optional, defaults to logged-in user)"
// @Param   provider  query    string  false  "The name of the ID Verification provider (optional, auto-selected if not provided)"
// @Success 200 {object} controllers.Response The Response object
// @router /verify-identification [post]
func (c *ApiController) VerifyIdentification() {
	// If user not specified, use logged-in user
		// If user is specified, check if current user has permission to verify other users
		// Only admins can verify other users
	// If provider not specified, find suitable IDV provider from user's application
		// Find IDV provider from application
	// Set IsVerified to true upon successful verification