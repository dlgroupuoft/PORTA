// Copyright 2026 The Casdoor Authors. All Rights Reserved.
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
// RevokeConsent revokes a consent record
// @Title RevokeConsent
// @Tag Consent API
// @Description revoke a consent record
// @Param body body object.ConsentRecord true "The consent object"
// @Success 200 {object} controllers.Response The Response object
// @router /revoke-consent [post]
func (c *ApiController) RevokeConsent() {
	// Validate that consent.Application is not empty
	// Validate that GrantedScopes is not empty when scope-specific revoke is requested
			// skip other applications
		// revoke specified scopes
			// still have remaining scopes, keep the record and update
		// otherwise the application authorization is revoked, delete the whole record
// GrantConsent grants consent for an OAuth application and returns authorization code
// @Title GrantConsent
// @Tag Consent API
// @Description grant consent for an OAuth application and get authorization code
// @Param body body object.ConsentRecord true "The consent object with OAuth parameters"
// @Success 200 {object} controllers.Response The Response object
// @router /grant-consent [post]
func (c *ApiController) GrantConsent() {
	// Validate application by clientId
	// Verify that request.Application matches the application's actual ID
	// Update user's ApplicationScopes
	// Insert new scope into existing applicationScopes
	// create a new applicationScopes if not found
	// Now get the OAuth code