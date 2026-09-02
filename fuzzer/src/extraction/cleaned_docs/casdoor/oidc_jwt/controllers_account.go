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
type Response struct {
type Captcha struct {
// this API is used by "Api URL" of Flarum's FoF Passport plugin
// https://github.com/FriendsOfFlarum/passport
type LaravelResponse struct {
// Signup
// @Tag Login API
// @Title Signup
// @Description sign up a new user
// @Param   username     formData    string  true        "The username to sign up"
// @Param   password     formData    string  true        "The password"
// @Success 200 {object} controllers.Response The Response object
// @router /signup [post]
func (c *ApiController) Signup() {
	// Check if this is an OAuth flow and automatically generate code
	// If OAuth parameters are present, generate OAuth code and return it
// Logout
// @Title Logout
// @Tag Login API
// @Description logout the current user
// @Param   id_token_hint   query        string  false        "id_token_hint"
// @Param   post_logout_redirect_uri    query    string  false     "post_logout_redirect_uri"
// @Param   state     query    string  false     "state"
// @Success 200 {object} controllers.Response The Response object
// @router /logout [post]
func (c *ApiController) Logout() {
	// https://openid.net/specs/openid-connect-rpinitiated-1_0-final.html
		// TODO https://github.com/casdoor/casdoor/pull/1494#discussion_r1095675265
		// "post_logout_redirect_uri" has been made optional, see: https://github.com/casdoor/casdoor/issues/2151
		// if redirectUri == "" {
		// 	c.ResponseError(c.T("general:Missing parameter") + ": post_logout_redirect_uri")
		// 	return
		// }
		// TODO https://github.com/casdoor/casdoor/pull/1494#discussion_r1095675265
// SsoLogout
// @Title SsoLogout
// @Tag Login API
// @Description logout the current user from all applications or current session only
// @Param   logoutAll   query    string  false     "Whether to logout from all sessions. Accepted values: 'true', '1', or empty (default: true). Any other value means false."
// @Success 200 {object} controllers.Response The Response object
// @router /sso-logout [get,post]
func (c *ApiController) SsoLogout() {
	// Check if user wants to logout from all sessions or just current session
	// Default is true for backward compatibility
	// Get tokens for notification (needed for both session-level and full logout)
	// This enables subsystems to identify and invalidate corresponding access tokens
	// Note: Tokens must be retrieved BEFORE expiration to include their hashes in the notification
		// Logout from all sessions: expire all tokens and delete all sessions
		// Logout from current session only
		// Only delete the current session's Beego session
	// Send SSO logout notifications to all notification providers in the user's signup application
	// Now includes session-level information for targeted logout
// GetAccount
// @Title GetAccount
// @Tag Account API
// @Description get the details of the current account
// @Success 200 {object} controllers.Response The Response object
// @router /get-account [get]
func (c *ApiController) GetAccount() {
// GetUserinfo
// UserInfo
// @Title UserInfo
// @Tag Account API
// @Description return user information according to OIDC standards
// @Success 200 {object} object.Userinfo The Response object
// @router /userinfo [get]
func (c *ApiController) GetUserinfo() {
// GetUserinfo2
// LaravelResponse
// @Title UserInfo2
// @Tag Account API
// @Description return Laravel compatible user information according to OAuth 2.0
// @Success 200 {object} controllers.LaravelResponse The Response object
// @router /user [get]
func (c *ApiController) GetUserinfo2() {
// GetCaptcha ...
// @Tag Login API
// @Title GetCaptcha
// @router /get-captcha [get]
// @Success 200 {object} object.Userinfo The Response object
func (c *ApiController) GetCaptcha() {
	// When isCurrentProvider == "true", the frontend passes a provider ID instead of an application ID.
	// In that case, skip application lookup and rule evaluation, and just return the provider config.
		// Check the CAPTCHA rule to determine if CAPTCHA should be shown
		// For Internet-Only rule, we can determine on the backend if CAPTCHA should be shown
		// For other rules (Dynamic, Always), we need to return the CAPTCHA config
			// For "None" rule, skip CAPTCHA
				// For Internet-Only rule, check if the client is from intranet
					// Client is from intranet, skip CAPTCHA
func (c *ApiController) deleteUserSession(user string) error {
	// Casdoor session ID derived from owner, username, and application
	// Explicitly get the Beego session ID from the context