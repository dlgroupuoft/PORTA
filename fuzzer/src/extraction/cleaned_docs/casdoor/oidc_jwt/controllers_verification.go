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
// GetVerifications
// @Title GetVerifications
// @Tag Verification API
// @Description get payments
// @Param   owner     query    string  true        "The owner of payments"
// @Success 200 {array} object.Verification The Response object
// @router /get-payments [get]
func (c *ApiController) GetVerifications() {
	// For global admin with organizationName parameter, use it to filter
	// For org admin, use their organization
// GetUserVerifications
// @Title GetUserVerifications
// @Tag Verification API
// @Description get payments for a user
// @Param   owner     query    string  true        "The owner of payments"
// @Param   organization    query   string  true   "The organization of the user"
// @Param   user    query   string  true           "The username of the user"
// @Success 200 {array} object.Verification The Response object
// @router /get-user-payments [get]
func (c *ApiController) GetUserVerifications() {
// GetVerification
// @Title GetVerification
// @Tag Verification API
// @Description get payment
// @Param   id     query    string  true        "The id ( owner/name ) of the payment"
// @Success 200 {object} object.Verification The Response object
// @router /get-payment [get]
func (c *ApiController) GetVerification() {
// SendVerificationCode ...
// @Title SendVerificationCode
// @Tag Verification API
// @router /send-verification-code [post]
// @Success 200 {object} object.Userinfo The Response object
func (c *ApiController) SendVerificationCode() {
	// Check if "Forgot password?" signin item is visible when using forget verification
		// Block access if the signin item is not found or is explicitly hidden
	// Try to resolve user for CAPTCHA rule checking
	// checkUser != "", means method is ForgetVerification
		// mfaUserSession != "", means method is MfaAuthVerification
		// For reset verification, get the current logged-in user
		// For login verification, try to find user by email/phone for CAPTCHA check
		// This is a preliminary lookup; the actual validation happens later in the switch statement
			// Prefer resolving the user directly by phone, consistent with the later login switch,
			// so that Dynamic CAPTCHA is not skipped due to missing/invalid country code.
	// Determine username for CAPTCHA check
	// Check if CAPTCHA should be enabled based on the rule (Dynamic/Always/Internet-Only)
	// Only verify CAPTCHA if it should be enabled
// VerifyCaptcha ...
// @Title VerifyCaptcha
// @Tag Verification API
// @router /verify-captcha [post]
// @Success 200 {object} object.Userinfo The Response object
func (c *ApiController) VerifyCaptcha() {
// ResetEmailOrPhone ...
// @Tag Account API
// @Title ResetEmailOrPhone
// @router /reset-email-or-phone [post]
// @Success 200 {object} object.Userinfo The Response object
func (c *ApiController) ResetEmailOrPhone() {
// VerifyCode
// @Tag Verification API
// @Title VerifyCode
// @router /verify-code [post]
// @Success 200 {object} object.Userinfo The Response object
func (c *ApiController) VerifyCode() {