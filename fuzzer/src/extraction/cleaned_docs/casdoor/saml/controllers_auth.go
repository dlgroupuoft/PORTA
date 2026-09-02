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
func codeToResponse(code *object.Code) *Response {
func tokenToResponse(token *object.Token) *Response {
// HandleLoggedIn ...
func (c *ApiController) HandleLoggedIn(application *object.Application, user *object.User, form *form.AuthForm) (resp *Response) {
	// check user's tag
		// only users with the tag that is listed in the application tags can login
		// supports comma-separated tags in user.Tag (e.g., "default-policy,project-admin")
	// check whether paid-user have active subscription
			// check pending subscription
			// paid-user does not have active or pending subscription, find the default pricing of application
				// let the paid-user select plan
			// The prompt page needs the user to be signed in
			// The prompt page needs the user to be signed in
		// not oauth but CAS SSO protocol
			// The prompt page needs the user to be signed in
	// For all successful logins, set the session expiration; if auto signin is not checked, cap it at 24 hours.
// GetApplicationLogin ...
// @Title GetApplicationLogin
// @Tag Login API
// @Description get application login
// @Param   clientId    query    string  true        "client id"
// @Param   responseType    query    string  true        "response type"
// @Param   redirectUri    query    string  true        "redirect uri"
// @Param   scope    query    string  true        "scope"
// @Param   state    query    string  true        "state"
// @Success 200 {object} controllers.Response The Response object
// @router /get-app-login [get]
func (c *ApiController) GetApplicationLogin() {
func setHttpClient(idProvider idp.IdProvider, providerType string) {
func isProxyProviderType(providerType string) bool {
func checkMfaEnable(c *ApiController, user *object.User, organization *object.Organization, verificationType string) bool {
		// The prompt page needs the user to be signed in
func getExistUserByBindingRule(providerItem *object.ProviderItem, application *object.Application, userInfo *idp.UserInfo) (user *object.User, err error) {
		// Find existing user with Email
		// Find existing user with phone number
		// Try to find existing user by username (case-insensitive)
		// This allows OAuth providers (e.g., Wecom) to automatically associate with
		// existing users when usernames match, particularly useful for enterprise
		// scenarios where signup is disabled and users already exist in Casdoor
// Login ...
// @Title Login
// @Tag Login API
// @Description login
// @Param clientId        query    string  true clientId
// @Param responseType    query    string  true responseType
// @Param redirectUri     query    string  true redirectUri
// @Param scope     query    string  false  scope
// @Param state     query    string  false  state
// @Param nonce     query    string  false nonce
// @Param code_challenge_method   query    string  false code_challenge_method
// @Param code_challenge          query    string  false code_challenge
// @Param   form   body   controllers.AuthForm  true        "Login information"
// @Success 200 {object} controllers.Response The Response object
// @router /login [post]
func (c *ApiController) Login() {
			// check result through Email or Phone
			// disable the verification code
			// SAML
			// OAuth
			// https://github.com/golang/oauth2/issues/123#issuecomment-103715338
				// The userInfo.Id is the NameID in SAML response, it could be name / email / phone
				// Sign in via OAuth (want to sign up but already have account)
				// sync info from 3rd-party if possible
				// Sign up via OAuth
					// Check and validate invitation code
					// Handle UseEmailAsUsername for OAuth and Web3
					// Handle username conflicts
					// Set group from invitation code if available, otherwise use provider's signup group or application's default group
					// Increment invitation usage count
				// sync info from 3rd-party if possible
				// TODO: since we get the user info from SAML response, we can try to create the user
			// resp = &Response{Status: "ok", Msg: "", Data: res}
			// sync info from 3rd-party if possible
			// user already signed in to Casdoor, so let the user click the avatar button to do the quick sign-in
func (c *ApiController) GetSamlLogin() {
func (c *ApiController) HandleSamlLogin() {
// HandleOfficialAccountEvent ...
// @Tag System API
// @Title HandleOfficialAccountEvent
// @router /webhook [POST]
// @Success 200 {object} controllers.Response The Response object
func (c *ApiController) HandleOfficialAccountEvent() {
// GetWebhookEventType ...
// @Tag System API
// @Title GetWebhookEventType
// @router /get-webhook-event [GET]
// @Param   ticket     query    string  true        "The eventId of QRCode"
// @Success 200 {object} controllers.Response The Response object
func (c *ApiController) GetWebhookEventType() {
// GetQRCode
// @Tag System API
// @Title GetWechatQRCode
// @router /get-qrcode [GET]
// @Param   id     query    string  true        "The id ( owner/name ) of provider"
// @Success 200 {object} controllers.Response The Response object
func (c *ApiController) GetQRCode() {
// GetCaptchaStatus
// @Title GetCaptchaStatus
// @Tag Token API
// @Description Get Login Error Counts
// @Param   id     query    string  true        "The id ( owner/name ) of user"
// @Success 200 {object} controllers.Response The Response object
// @router /get-captcha-status [get]
func (c *ApiController) GetCaptchaStatus() {
// Callback
// @Title Callback
// @Tag Callback API
// @Description Get Login Error Counts
// @router /Callback [post]
// @Success 200 {object} object.Userinfo The Response object
func (c *ApiController) Callback() {
// DeviceAuth
// @Title DeviceAuth
// @Tag Device Authorization Endpoint
// @Description Endpoint for the device authorization flow
// @router /device-auth [post]
// @Success 200 {object} object.DeviceAuthResponse The Response object
func (c *ApiController) DeviceAuth() {